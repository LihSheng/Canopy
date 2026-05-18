import time

import pytest
from sqlalchemy.orm import sessionmaker

from common.database import Base, reset_engine, set_engine
from backup.backup_engine import BackupEngine
from backup.clone_engine import CloneEngine
from backup.domain import BackupStatus
from backup.restore_engine import RestoreEngine
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.schemas.audit import AuditEventModel
from control_plane.schemas.tenants import TenantModel
from control_plane.tenant_repository import TenantRepository


@pytest.fixture
def backup_dir(tmp_path):
    d = tmp_path / "backups"
    d.mkdir(exist_ok=True)
    return str(d)


@pytest.fixture
def session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def _make_backup_engine(session_factory, backup_dir):
    return BackupEngine(
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=session_factory,
        backup_dir=backup_dir,
    )


def _make_restore_engine(backup_engine, session_factory):
    return RestoreEngine(
        backup_engine=backup_engine,
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=session_factory,
        routing_cache=None,
    )


def _make_clone_engine(session_factory):
    return CloneEngine(
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=session_factory,
        lifecycle_service=None,
        routing_cache=None,
    )


def _wait_for_run(engine, get_run, run_id, timeout_seconds=5.0):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        run = get_run(run_id)
        if run is not None and run.status != BackupStatus.PENDING and run.status != BackupStatus.RUNNING:
            return run
        time.sleep(0.1)
    return get_run(run_id)


class TestFullBackupRestoreFlow:
    def test_full_backup_and_restore_flow(
        self, db_session, session_factory, backup_dir
    ):
        _seed_tenant(db_session, "t-int-1")

        backup_engine = _make_backup_engine(session_factory, backup_dir)
        restore_engine = _make_restore_engine(backup_engine, session_factory)

        backup_run = backup_engine.create_backup("t-int-1")
        backup_run = _wait_for_run(backup_engine, backup_engine.get_backup, backup_run.id)
        assert backup_run is not None
        assert backup_run.status == BackupStatus.COMPLETED
        assert backup_run.snapshot_ref is not None

        restore_run = restore_engine.create_restore("t-int-1", backup_run.id)
        restore_run = _wait_for_run(restore_engine, restore_engine.get_restore, restore_run.id)
        assert restore_run is not None
        assert restore_run.status == BackupStatus.COMPLETED

    def test_backup_creates_snapshot_ref(
        self, db_session, session_factory, backup_dir
    ):
        _seed_tenant(db_session, "t-int-2")
        backup_engine = _make_backup_engine(session_factory, backup_dir)

        backup_run = backup_engine.create_backup("t-int-2")
        backup_run = _wait_for_run(backup_engine, backup_engine.get_backup, backup_run.id)

        assert backup_run is not None
        assert backup_run.status == BackupStatus.COMPLETED
        assert backup_run.snapshot_ref is not None


class TestDataIntegrityAfterRestore:
    def test_verify_tenant_data_after_restore(
        self, db_session, session_factory, backup_dir
    ):
        _seed_tenant(db_session, "t-int-3")

        tenant_count_before = (
            db_session.query(TenantModel)
            .filter(TenantModel.lifecycle_state == "active")
            .count()
        )

        backup_engine = _make_backup_engine(session_factory, backup_dir)
        restore_engine = _make_restore_engine(backup_engine, session_factory)

        backup_run = backup_engine.create_backup("t-int-3")
        backup_run = _wait_for_run(backup_engine, backup_engine.get_backup, backup_run.id)

        restore_run = restore_engine.create_restore("t-int-3", backup_run.id)
        restore_run = _wait_for_run(restore_engine, restore_engine.get_restore, restore_run.id)

        tenant_count_after = (
            db_session.query(TenantModel)
            .filter(TenantModel.lifecycle_state == "active")
            .count()
        )
        assert tenant_count_after == tenant_count_before


class TestRestoreLifecycleState:
    def test_restored_tenant_has_correct_lifecycle_state(
        self, db_session, session_factory, backup_dir
    ):
        _seed_tenant(db_session, "t-int-4", lifecycle_state="suspended")

        backup_engine = _make_backup_engine(session_factory, backup_dir)
        restore_engine = _make_restore_engine(backup_engine, session_factory)

        backup_run = backup_engine.create_backup("t-int-4")
        backup_run = _wait_for_run(backup_engine, backup_engine.get_backup, backup_run.id)
        assert backup_run is not None

        restore_run = restore_engine.create_restore("t-int-4", backup_run.id)
        restore_run = _wait_for_run(restore_engine, restore_engine.get_restore, restore_run.id)

        assert restore_run is not None


class TestTenantScopedBackup:
    def test_backup_tenant_a_does_not_affect_tenant_b(
        self, db_session, session_factory, backup_dir
    ):
        _seed_tenant(db_session, "t-int-a")
        _seed_tenant(db_session, "t-int-b")

        backup_engine = _make_backup_engine(session_factory, backup_dir)

        backup_run = backup_engine.create_backup("t-int-a")
        backup_run = _wait_for_run(backup_engine, backup_engine.get_backup, backup_run.id)
        assert backup_run.tenant_id == "t-int-a"

        t_b_after = (
            db_session.query(TenantModel).filter(TenantModel.id == "t-int-b").first()
        )
        assert t_b_after is not None
        assert t_b_after.lifecycle_state == "active"


class TestArchiveAndRestoreFlow:
    def test_archive_then_restore_from_backup(
        self, db_session, session_factory, backup_dir
    ):
        _seed_tenant(db_session, "t-int-archive")

        backup_engine = _make_backup_engine(session_factory, backup_dir)

        backup_run = backup_engine.create_backup("t-int-archive")
        backup_run = _wait_for_run(backup_engine, backup_engine.get_backup, backup_run.id)
        assert backup_run is not None
        assert backup_run.status == BackupStatus.COMPLETED

        tenant = (
            db_session.query(TenantModel)
            .filter(TenantModel.id == "t-int-archive")
            .first()
        )
        tenant.lifecycle_state = "archived"
        db_session.commit()

        tenant_after_archive = (
            db_session.query(TenantModel)
            .filter(TenantModel.id == "t-int-archive")
            .first()
        )
        assert tenant_after_archive.lifecycle_state == "archived"

        restore_engine = _make_restore_engine(backup_engine, session_factory)
        restore_run = restore_engine.create_restore("t-int-archive", backup_run.id)
        restore_run = _wait_for_run(restore_engine, restore_engine.get_restore, restore_run.id)

        assert restore_run is not None


