import pytest

from v5.control_plane.schemas.audit import AuditEventModel, ImpersonationSessionModel
from v5.control_plane.schemas.config import TenantConfigModel
from v5.control_plane.schemas.database_targets import TenantDatabaseTargetModel
from v5.control_plane.schemas.jobs import ProvisioningJobModel
from v5.control_plane.schemas.memberships import TenantMembershipModel
from v5.control_plane.schemas.tenants import TenantModel


class TestTenantLifecycleStates:
    def test_tenant_created_in_pending_state(self, db_session):
        tenant = TenantModel(
            id="t-life-1",
            tenant_uuid="tuuid-life-1",
            name="Lifecycle Test",
            slug="lifecycle-test",
        )
        db_session.add(tenant)
        db_session.commit()
        assert tenant.lifecycle_state == "pending"

    def test_transition_pending_to_active(self, db_session):
        tenant = TenantModel(
            id="t-life-2",
            tenant_uuid="tuuid-life-2",
            name="Pending Co",
            slug="pending-co",
            lifecycle_state="pending",
        )
        db_session.add(tenant)
        db_session.commit()

        tenant.lifecycle_state = "active"
        db_session.commit()

        fetched = db_session.query(TenantModel).filter(TenantModel.id == "t-life-2").first()
        assert fetched.lifecycle_state == "active"

    def test_transition_active_to_suspended(self, db_session):
        tenant = TenantModel(
            id="t-life-3",
            tenant_uuid="tuuid-life-3",
            name="Active Co",
            slug="active-co",
            lifecycle_state="active",
        )
        db_session.add(tenant)
        db_session.commit()

        tenant.lifecycle_state = "suspended"
        db_session.commit()

        fetched = db_session.query(TenantModel).filter(TenantModel.id == "t-life-3").first()
        assert fetched.lifecycle_state == "suspended"

    def test_transition_suspended_to_active(self, db_session):
        tenant = TenantModel(
            id="t-life-4",
            tenant_uuid="tuuid-life-4",
            name="Suspended Co",
            slug="suspended-co-life",
            lifecycle_state="suspended",
        )
        db_session.add(tenant)
        db_session.commit()

        tenant.lifecycle_state = "active"
        db_session.commit()

        fetched = db_session.query(TenantModel).filter(TenantModel.id == "t-life-4").first()
        assert fetched.lifecycle_state == "active"

    def test_transition_active_to_archived(self, db_session):
        tenant = TenantModel(
            id="t-life-5",
            tenant_uuid="tuuid-life-5",
            name="Archive Co",
            slug="archive-co",
            lifecycle_state="active",
        )
        db_session.add(tenant)
        db_session.commit()

        tenant.lifecycle_state = "archived"
        db_session.commit()

        fetched = db_session.query(TenantModel).filter(TenantModel.id == "t-life-5").first()
        assert fetched.lifecycle_state == "archived"

    def test_transition_archived_to_active(self, db_session):
        tenant = TenantModel(
            id="t-life-6",
            tenant_uuid="tuuid-life-6",
            name="Restorable Co",
            slug="restorable-co",
            lifecycle_state="archived",
        )
        db_session.add(tenant)
        db_session.commit()

        tenant.lifecycle_state = "active"
        db_session.commit()

        fetched = db_session.query(TenantModel).filter(TenantModel.id == "t-life-6").first()
        assert fetched.lifecycle_state == "active"

    def test_tenant_has_uuid(self, db_session):
        tenant = TenantModel(
            id="t-life-7",
            tenant_uuid="12345678-1234-1234-1234-123456789abc",
            name="UUID Co",
            slug="uuid-co",
        )
        db_session.add(tenant)
        db_session.commit()
        assert len(tenant.tenant_uuid) == 36
        assert "-" in tenant.tenant_uuid

    def test_unique_slug_enforced(self, db_session):
        t1 = TenantModel(
            id="t-unique-1",
            tenant_uuid="tuuid-unique-1",
            name="First",
            slug="unique-slug",
        )
        t2 = TenantModel(
            id="t-unique-2",
            tenant_uuid="tuuid-unique-2",
            name="Second",
            slug="unique-slug",
        )
        db_session.add(t1)
        db_session.commit()
        db_session.add(t2)
        with pytest.raises(Exception):
            db_session.commit()


class TestConfigVersioning:
    def test_set_config_creates_version_1(self, db_session):
        config = TenantConfigModel(
            id="cfg-1",
            tenant_id="t-1",
            config_key="storage_limit",
            config_value_json='{"max_bytes": 10737418240}',
            version_number=1,
        )
        db_session.add(config)
        db_session.commit()
        assert config.version_number == 1

    def test_set_config_bumps_version(self, db_session):
        v1 = TenantConfigModel(
            id="cfg-v1",
            tenant_id="t-2",
            config_key="storage_limit",
            config_value_json='{"max_bytes": 5000000000}',
            version_number=1,
        )
        db_session.add(v1)
        db_session.commit()

        v2 = TenantConfigModel(
            id="cfg-v2",
            tenant_id="t-2",
            config_key="storage_limit",
            config_value_json='{"max_bytes": 10737418240}',
            version_number=2,
        )
        db_session.add(v2)
        db_session.commit()

        configs = (
            db_session.query(TenantConfigModel)
            .filter(
                TenantConfigModel.tenant_id == "t-2",
                TenantConfigModel.config_key == "storage_limit",
            )
            .order_by(TenantConfigModel.version_number.desc())
            .all()
        )
        assert len(configs) == 2
        assert configs[0].version_number == 2
        assert configs[1].version_number == 1

    def test_config_history_preserves_all_versions(self, db_session):
        for i, val in enumerate(["v1_value", "v2_value", "v3_value"], start=1):
            cfg = TenantConfigModel(
                id=f"cfg-hist-{i}",
                tenant_id="t-history",
                config_key="feature_flags",
                config_value_json=f'{{"flag": "{val}"}}',
                version_number=i,
            )
            db_session.add(cfg)
        db_session.commit()

        history = (
            db_session.query(TenantConfigModel)
            .filter(
                TenantConfigModel.tenant_id == "t-history",
                TenantConfigModel.config_key == "feature_flags",
            )
            .order_by(TenantConfigModel.version_number.desc())
            .all()
        )
        assert len(history) == 3


class TestMembershipRoles:
    def test_default_role_is_member(self, db_session):
        m = TenantMembershipModel(
            id="mem-1",
            user_id="user-1",
            tenant_id="tenant-1",
        )
        db_session.add(m)
        db_session.commit()
        assert m.role == "member"

    def test_owner_role(self, db_session):
        m = TenantMembershipModel(
            id="mem-2",
            user_id="user-2",
            tenant_id="tenant-1",
            role="owner",
        )
        db_session.add(m)
        db_session.commit()
        assert m.role == "owner"

    def test_admin_role(self, db_session):
        m = TenantMembershipModel(
            id="mem-3",
            user_id="user-3",
            tenant_id="tenant-1",
            role="admin",
        )
        db_session.add(m)
        db_session.commit()
        assert m.role == "admin"

    def test_member_role(self, db_session):
        m = TenantMembershipModel(
            id="mem-4",
            user_id="user-4",
            tenant_id="tenant-1",
            role="member",
        )
        db_session.add(m)
        db_session.commit()
        assert m.role == "member"

    def test_membership_status_default_active(self, db_session):
        m = TenantMembershipModel(
            id="mem-5",
            user_id="user-5",
            tenant_id="tenant-1",
        )
        db_session.add(m)
        db_session.commit()
        assert m.status == "active"


class TestAuditEvent:
    def test_create_audit_event(self, db_session):
        event = AuditEventModel(
            id="audit-1",
            tenant_id="t-1",
            actor_user_id="user-1",
            event_type="tenant.created",
        )
        db_session.add(event)
        db_session.commit()
        assert event.event_type == "tenant.created"
        assert event.tenant_id == "t-1"
        assert event.actor_user_id == "user-1"

    def test_audit_event_with_payload(self, db_session):
        event = AuditEventModel(
            id="audit-2",
            tenant_id="t-2",
            actor_user_id="user-2",
            event_type="tenant.suspended",
            event_payload_json='{"reason": "billing", "tenant_name": "Test Co"}',
        )
        db_session.add(event)
        db_session.commit()
        assert event.event_payload_json is not None
        assert "billing" in event.event_payload_json

    def test_audit_event_without_tenant_id(self, db_session):
        event = AuditEventModel(
            id="audit-3",
            tenant_id=None,
            actor_user_id="user-3",
            event_type="platform.startup",
        )
        db_session.add(event)
        db_session.commit()
        assert event.tenant_id is None

    def test_impersonation_session(self, db_session):
        session = ImpersonationSessionModel(
            id="imp-1",
            platform_admin_user_id="admin-1",
            tenant_id="t-1",
            reason="Support request #1234",
        )
        db_session.add(session)
        db_session.commit()
        assert session.status == "active"
        assert session.reason == "Support request #1234"
        assert session.platform_admin_user_id == "admin-1"
