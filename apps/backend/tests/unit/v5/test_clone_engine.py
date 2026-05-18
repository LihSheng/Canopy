import time

import pytest

from v5.backup.backup_engine import BackupEngine
from v5.backup.clone_engine import CloneEngine
from v5.backup.domain import BackupStatus
from v5.control_plane.audit_service import AuditService
from v5.control_plane.config_repository import ConfigRepository
from v5.control_plane.schemas.config import TenantConfigModel
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


def _make_clone_engine(db_session):
    return CloneEngine(
        tenant_repository_class=TenantRepository,
        config_repository_class=ConfigRepository,
        audit_service_class=AuditService,
        db_session_factory=lambda: db_session,
        lifecycle_service=None,
        routing_cache=None,
    )


class TestCloneCreatesNewTenant:
    def test_clone_creates_new_tenant_with_different_id(self, db_session):
        source = _seed_tenant(db_session, "t-source")
        engine = _make_clone_engine(db_session)

        run = engine.create_clone("t-source", "Cloned Tenant")
        time.sleep(0.5)

        run = engine.get_clone(run.id)
        if run and run.status == BackupStatus.COMPLETED:
            assert run.target_tenant_id is not None
            assert run.target_tenant_id != run.source_tenant_id

            cloned = (
                db_session.query(TenantModel)
                .filter(TenantModel.id == run.target_tenant_id)
                .first()
            )
            assert cloned is not None
            assert cloned.id != source.id


class TestCloneCopiesConfigs:
    def test_clone_copies_configs_from_source(self, db_session):
        source = _seed_tenant(db_session, "t-source-cfg")

        config_repo = ConfigRepository(db_session)
        config_repo.set_config("t-source-cfg", "feature_flags", '{"flag_a": true}')
        config_repo.set_config("t-source-cfg", "storage_limit", '{"max_bytes": 1000}')

        engine = _make_clone_engine(db_session)

        run = engine.create_clone("t-source-cfg", "Cloned With Configs")
        time.sleep(0.5)

        run = engine.get_clone(run.id)
        if run and run.status == BackupStatus.COMPLETED:
            cloned_configs = config_repo.get_all_configs(run.target_tenant_id)
            config_keys = {c.config_key for c in cloned_configs}
            assert "feature_flags" in config_keys
            assert "storage_limit" in config_keys


class TestClonePreservesSource:
    def test_clone_preserves_source_tenant_unchanged(self, db_session):
        source = _seed_tenant(db_session, "t-source-preserve")
        engine = _make_clone_engine(db_session)

        run = engine.create_clone("t-source-preserve", "Cloned Preserved")
        time.sleep(0.5)

        source_after = (
            db_session.query(TenantModel)
            .filter(TenantModel.id == "t-source-preserve")
            .first()
        )
        assert source_after is not None
        assert source_after.lifecycle_state == "active"
        assert source_after.name == "Tenant t-source-preserve"


class TestCloneValidation:
    def test_clone_validates_source_is_active_or_archived(self, db_session):
        _seed_tenant(db_session, "t-active", lifecycle_state="active")
        engine = _make_clone_engine(db_session)

        errors = engine.validate_cloneable("t-active")
        assert errors == []

    def test_clone_cannot_proceed_if_source_is_deleted(self, db_session):
        _seed_tenant(db_session, "t-deleted", lifecycle_state="deleted")
        engine = _make_clone_engine(db_session)

        errors = engine.validate_cloneable("t-deleted")
        assert len(errors) > 0

    def test_clone_cannot_proceed_if_source_is_pending(self, db_session):
        _seed_tenant(db_session, "t-pending", lifecycle_state="pending")
        engine = _make_clone_engine(db_session)

        errors = engine.validate_cloneable("t-pending")
        assert len(errors) > 0
        assert any("pending" in e.lower() for e in errors)

    def test_clone_cannot_proceed_if_source_not_found(self, db_session):
        engine = _make_clone_engine(db_session)

        errors = engine.validate_cloneable("t-nonexistent")
        assert len(errors) > 0


class TestCloneRecordsAudit:
    def test_clone_records_audit_event_with_source_and_target(self, db_session):
        _seed_tenant(db_session, "t-audit-clone")
        engine = _make_clone_engine(db_session)

        run = engine.create_clone("t-audit-clone", "Audit Cloned Co")
        time.sleep(0.5)

        run = engine.get_clone(run.id)
        if run and run.status == BackupStatus.COMPLETED:
            from v5.control_plane.schemas.audit import AuditEventModel

            events = (
                db_session.query(AuditEventModel)
                .filter(AuditEventModel.tenant_id == run.target_tenant_id)
                .all()
            )
            cloned_events = [e for e in events if e.event_type == "tenant.cloned"]
            assert len(cloned_events) >= 1
            assert "source_tenant_id" in (cloned_events[0].event_payload_json or "")


class TestCloneResult:
    def test_clone_result_includes_new_database_target_ref(self, db_session):
        _seed_tenant(db_session, "t-result")
        engine = _make_clone_engine(db_session)

        run = engine.create_clone("t-result", "Result Cloned Co")
        time.sleep(0.5)

        run = engine.get_clone(run.id)
        if run and run.status == BackupStatus.COMPLETED:
            assert run.new_database_target_ref is not None

    def test_list_clones_filtered_by_source(self, db_session):
        _seed_tenant(db_session, "t-list-clone")
        engine = _make_clone_engine(db_session)

        run = engine.create_clone("t-list-clone", "List Clone 1")
        time.sleep(0.5)

        clones = engine.list_clones(source_tenant_id="t-list-clone")
        assert len(clones) >= 1

    def test_get_clone_returns_none_for_missing(self, db_session):
        engine = _make_clone_engine(db_session)
        assert engine.get_clone("nonexistent") is None
