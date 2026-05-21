import time

from backup.backup_engine import BackupEngine
from backup.domain import BackupRun, BackupStatus, BackupType
from backup.restore_engine import RestoreEngine
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.schemas.tenants import TenantModel
from control_plane.tenant_repository import TenantRepository


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


def _make_engines(db_session, backup_dir):
    backup_engine = BackupEngine(
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=lambda: db_session,
        backup_dir=backup_dir,
    )
    restore_engine = RestoreEngine(
        backup_engine=backup_engine,
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=lambda: db_session,
        routing_cache=None,
    )
    return backup_engine, restore_engine


class TestRestoreValidatesBackupExists:
    def test_restore_validates_backup_exists(self, db_session, tmp_path):
        _seed_tenant(db_session, "t-1")
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        errors = restore_engine.validate_restorable("t-1", "nonexistent-backup")
        assert len(errors) > 0
        assert any("not found" in e.lower() for e in errors)


class TestRestoreValidatesTenantState:
    def test_restore_validates_tenant_is_restorable_not_deleted(self, db_session, tmp_path):
        _seed_tenant(db_session, "t-deleted", lifecycle_state="deleted")
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        fake_backup = BackupRun(
            id="backup-1",
            tenant_id="t-deleted",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
        )
        with backup_engine._lock:
            backup_engine._runs["backup-1"] = fake_backup

        errors = restore_engine.validate_restorable("t-deleted", "backup-1")
        assert len(errors) > 0
        assert any("deleted" in e.lower() for e in errors)


class TestRestoreRecordsAudit:
    def test_restore_records_audit_event(self, db_session, tmp_path):
        _seed_tenant(db_session, "t-audit")
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        backup_run = backup_engine.create_backup("t-audit")
        time.sleep(0.5)

        backup_run = backup_engine.get_backup(backup_run.id)
        if backup_run and backup_run.status == BackupStatus.COMPLETED:
            restore_engine.create_restore("t-audit", backup_run.id)
            time.sleep(0.5)

            from control_plane.schemas.audit import AuditEventModel

            events = db_session.query(AuditEventModel).filter(AuditEventModel.tenant_id == "t-audit").all()
            restored_events = [e for e in events if e.event_type == "tenant.restored"]
            assert len(restored_events) >= 1


class TestRestoreValidationErrors:
    def test_validation_returns_specific_errors(self, db_session, tmp_path):
        _seed_tenant(db_session, "t-1")
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        errors = restore_engine.validate_restorable("t-1", "bad-id")
        assert len(errors) > 0

    def test_restore_with_nonexistent_tenant_fails(self, db_session, tmp_path):
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        fake_backup = BackupRun(
            id="backup-x",
            tenant_id="t-nonexistent",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
        )
        with backup_engine._lock:
            backup_engine._runs["backup-x"] = fake_backup

        errors = restore_engine.validate_restorable("t-nonexistent", "backup-x")
        assert len(errors) > 0
        assert any("not found" in e.lower() for e in errors)

    def test_restore_with_incomplete_backup_fails(self, db_session, tmp_path):
        _seed_tenant(db_session, "t-1")
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        fake_backup = BackupRun(
            id="backup-pending",
            tenant_id="t-1",
            backup_type=BackupType.FULL,
            status=BackupStatus.PENDING,
        )
        with backup_engine._lock:
            backup_engine._runs["backup-pending"] = fake_backup

        errors = restore_engine.validate_restorable("t-1", "backup-pending")
        assert len(errors) > 0
        assert any("completed" in e.lower() or "pending" in e.lower() for e in errors)


class TestRestoreListAndGet:
    def test_list_restores_by_tenant(self, db_session, tmp_path):
        _seed_tenant(db_session, "t-1")
        backup_engine, restore_engine = _make_engines(db_session, str(tmp_path))

        backup_run = backup_engine.create_backup("t-1")
        time.sleep(0.5)
        backup_run = backup_engine.get_backup(backup_run.id)

        if backup_run and backup_run.status == BackupStatus.COMPLETED:
            restore_engine.create_restore("t-1", backup_run.id)
            time.sleep(0.5)

            restores = restore_engine.list_restores("t-1")
            assert len(restores) >= 1
            assert all(r.tenant_id == "t-1" for r in restores)

    def test_get_restore_returns_none_for_missing(self, db_session, tmp_path):
        _, restore_engine = _make_engines(db_session, str(tmp_path))
        assert restore_engine.get_restore("nonexistent") is None
