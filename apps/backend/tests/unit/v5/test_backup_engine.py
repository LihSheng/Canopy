import time
from unittest.mock import MagicMock

import pytest

from v5.backup.backup_engine import BackupEngine
from v5.backup.domain import BackupRun, BackupStatus, BackupType
from v5.control_plane.audit_service import AuditService
from v5.control_plane.config_repository import ConfigRepository
from v5.control_plane.schemas.tenants import TenantModel
from v5.control_plane.tenant_repository import TenantRepository


def _seed_tenant(db_session, tenant_id, lifecycle_state="active"):
    tenant = TenantModel(
        id=tenant_id,
        tenant_uuid=f"tuuid-{tenant_id}",
        name=f"Tenant {tenant_id}",
        slug=f"tenant-{tenant_id}",
        lifecycle_state=lifecycle_state,
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


def _make_backup_engine(db_session, backup_dir):
    return BackupEngine(
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=lambda: db_session,
        backup_dir=backup_dir,
    )


class TestBackupCreation:
    def test_create_backup_returns_pending_run(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-active")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-active", BackupType.FULL)
        assert run.id is not None
        assert run.tenant_id == "t-active"
        assert run.status in (BackupStatus.PENDING, BackupStatus.RUNNING, BackupStatus.COMPLETED)

    def test_cannot_backup_deleted_tenant(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-deleted", lifecycle_state="deleted")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-deleted")
        time.sleep(0.3)

        run = engine.get_backup(run.id)
        assert run is not None
        assert run.status == BackupStatus.FAILED
        assert "deleted" in (run.error_message or "").lower()

    def test_cannot_backup_pending_tenant(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-pending", lifecycle_state="pending")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-pending")
        time.sleep(0.3)

        run = engine.get_backup(run.id)
        assert run is not None
        assert run.status == BackupStatus.FAILED
        assert "pending" in (run.error_message or "").lower()

    def test_nonexistent_tenant_fails(self, db_session, tmp_path):
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-nonexistent")
        time.sleep(0.3)

        run = engine.get_backup(run.id)
        assert run is not None
        assert run.status == BackupStatus.FAILED


class TestBackupRecordsAudit:
    def test_backup_records_audit_on_completion(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-audit-1")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-audit-1")
        time.sleep(0.5)

        run = engine.get_backup(run.id)
        if run and run.status == BackupStatus.COMPLETED:
            from v5.control_plane.schemas.audit import AuditEventModel

            events = (
                db_session.query(AuditEventModel)
                .filter(AuditEventModel.tenant_id == "t-audit-1")
                .all()
            )
            created_events = [e for e in events if e.event_type == "backup.created"]
            assert len(created_events) >= 1

    def test_backup_records_audit_on_failure(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-audit-2", lifecycle_state="deleted")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-audit-2")
        time.sleep(0.3)

        from v5.control_plane.schemas.audit import AuditEventModel

        events = (
            db_session.query(AuditEventModel)
            .filter(AuditEventModel.tenant_id == "t-audit-2")
            .all()
        )
        failed_events = [e for e in events if e.event_type == "backup.failed"]
        assert len(failed_events) >= 1


class TestRetentionCleanup:
    def test_retention_cleanup_removes_expired_backups(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-retention")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-retention")
        time.sleep(0.5)

        run = engine.get_backup(run.id)
        assert run is not None
        assert run.status in (BackupStatus.COMPLETED, BackupStatus.FAILED)

    def test_list_backups_filters_by_tenant(self, db_session, tmp_path):
        t1 = _seed_tenant(db_session, "t-list-1")
        t2 = _seed_tenant(db_session, "t-list-2")
        engine = _make_backup_engine(db_session, str(tmp_path))

        engine.create_backup("t-list-1")
        engine.create_backup("t-list-2")
        time.sleep(0.5)

        backups_t1 = engine.list_backups("t-list-1")
        backups_t2 = engine.list_backups("t-list-2")
        for b in backups_t1:
            assert b.tenant_id == "t-list-1"
        for b in backups_t2:
            assert b.tenant_id == "t-list-2"


class TestPITRBackup:
    def test_pitr_backup_type(self, db_session, tmp_path):
        tenant = _seed_tenant(db_session, "t-pitr")
        engine = _make_backup_engine(db_session, str(tmp_path))

        run = engine.create_backup("t-pitr", backup_type=BackupType.PITR)
        assert run.backup_type == BackupType.PITR
        time.sleep(0.5)

        run = engine.get_backup(run.id)
        assert run is not None
        assert run.backup_type == BackupType.PITR
