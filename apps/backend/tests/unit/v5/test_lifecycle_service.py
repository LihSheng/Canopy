import pytest

from common.errors import ValidationError
from v5.control_plane.audit_service import AuditService
from v5.control_plane.lifecycle_service import LifecycleService
from v5.control_plane.schemas.audit import AuditEventModel
from v5.control_plane.schemas.tenants import TenantModel


@pytest.fixture
def seed_tenant_for_lifecycle(db_session):
    tenant = TenantModel(
        id="t-lifecycle-1",
        tenant_uuid="tuuid-lifecycle-1",
        name="Lifecycle Tenant",
        slug="lifecycle-tenant",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def lifecycle_service(db_session):
    return LifecycleService(db_session)


class TestSuspendTenant:
    def test_suspend_active_tenant(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        tenant = lifecycle_service.suspend_tenant("t-lifecycle-1", "user-admin-1")
        assert tenant.lifecycle_state == "suspended"

    def test_suspend_creates_audit_event(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        lifecycle_service.suspend_tenant("t-lifecycle-1", "user-admin-1")
        events = (
            db_session.query(AuditEventModel)
            .filter(AuditEventModel.tenant_id == "t-lifecycle-1")
            .all()
        )
        suspended_events = [e for e in events if e.event_type == "tenant.suspended"]
        assert len(suspended_events) == 1
        assert suspended_events[0].actor_user_id == "user-admin-1"

    def test_suspend_already_suspended_raises(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        lifecycle_service.suspend_tenant("t-lifecycle-1", "user-admin-1")
        with pytest.raises(ValidationError, match="Cannot suspend"):
            lifecycle_service.suspend_tenant("t-lifecycle-1", "user-admin-1")

    def test_suspend_nonexistent_tenant(self, db_session, lifecycle_service):
        with pytest.raises(ValidationError, match="Tenant not found"):
            lifecycle_service.suspend_tenant("nonexistent", "user-admin-1")


class TestRestoreTenant:
    def test_restore_suspended_tenant(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        lifecycle_service.suspend_tenant("t-lifecycle-1", "user-admin-1")
        tenant = lifecycle_service.restore_tenant("t-lifecycle-1", "user-admin-1")
        assert tenant.lifecycle_state == "active"

    def test_restore_archived_tenant(self, db_session, lifecycle_service):
        tenant = TenantModel(
            id="t-archived-1",
            tenant_uuid="tuuid-archived-1",
            name="Archived Tenant",
            slug="archived-tenant",
            lifecycle_state="archived",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()

        restored = lifecycle_service.restore_tenant("t-archived-1", "user-admin-1")
        assert restored.lifecycle_state == "active"

    def test_restore_creates_audit_event(self, db_session, lifecycle_service):
        tenant = TenantModel(
            id="t-archived-2",
            tenant_uuid="tuuid-archived-2",
            name="Archived Co 2",
            slug="archived-co-2",
            lifecycle_state="archived",
            status="active",
        )
        db_session.add(tenant)
        db_session.commit()

        lifecycle_service.restore_tenant("t-archived-2", "user-admin-1")
        events = (
            db_session.query(AuditEventModel)
            .filter(AuditEventModel.tenant_id == "t-archived-2")
            .all()
        )
        restored_events = [e for e in events if e.event_type == "tenant.restored"]
        assert len(restored_events) == 1

    def test_restore_already_active_raises(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        with pytest.raises(ValidationError, match="Cannot restore"):
            lifecycle_service.restore_tenant("t-lifecycle-1", "user-admin-1")


class TestArchiveTenant:
    def test_archive_active_tenant(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        tenant = lifecycle_service.archive_tenant("t-lifecycle-1", "user-admin-1")
        assert tenant.lifecycle_state == "archived"

    def test_archive_suspended_tenant(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        lifecycle_service.suspend_tenant("t-lifecycle-1", "user-admin-1")
        tenant = lifecycle_service.archive_tenant("t-lifecycle-1", "user-admin-1")
        assert tenant.lifecycle_state == "archived"

    def test_archive_creates_audit_event(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        lifecycle_service.archive_tenant("t-lifecycle-1", "user-admin-1")
        events = (
            db_session.query(AuditEventModel)
            .filter(AuditEventModel.tenant_id == "t-lifecycle-1")
            .all()
        )
        archived_events = [e for e in events if e.event_type == "tenant.archived"]
        assert len(archived_events) == 1

    def test_archive_already_archived_raises(self, db_session, seed_tenant_for_lifecycle, lifecycle_service):
        lifecycle_service.archive_tenant("t-lifecycle-1", "user-admin-1")
        with pytest.raises(ValidationError, match="Cannot archive"):
            lifecycle_service.archive_tenant("t-lifecycle-1", "user-admin-1")
