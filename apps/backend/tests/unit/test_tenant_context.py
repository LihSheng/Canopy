from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from common.errors import AuthError
from context.membership_validator import MembershipValidator
from context.tenant_context import (
    TenantContext,
    get_current_tenant_context,
    reset_tenant_context,
    set_current_tenant_context,
)


class TestTenantContextVar:
    def test_create_and_set_context(self):
        ctx = TenantContext(
            tenant_id="t1",
            tenant_role="admin",
            membership_status="active",
        )
        set_current_tenant_context(ctx)
        result = get_current_tenant_context()
        assert result is not None
        assert result.tenant_id == "t1"
        assert result.tenant_role == "admin"
        assert result.membership_status == "active"
        assert result.is_impersonated is False

    def test_get_none_when_not_set(self):
        reset_tenant_context()
        result = get_current_tenant_context()
        assert result is None

    def test_reset_clears_context(self):
        ctx = TenantContext(
            tenant_id="t1",
            tenant_role="member",
            membership_status="active",
        )
        set_current_tenant_context(ctx)
        assert get_current_tenant_context() is not None
        reset_tenant_context()
        assert get_current_tenant_context() is None

    def test_context_fields_defaults(self):
        ctx = TenantContext(
            tenant_id="t2",
            tenant_role="owner",
            membership_status="active",
        )
        assert ctx.database_target_ref is None
        assert ctx.active_token_id is None
        assert ctx.is_impersonated is False

    def test_context_with_impersonation(self):
        ctx = TenantContext(
            tenant_id="t3",
            tenant_role="member",
            membership_status="active",
            is_impersonated=True,
            active_token_id="imp-token-1",
        )
        assert ctx.is_impersonated is True
        assert ctx.active_token_id == "imp-token-1"


class TestMembershipValidator:
    def test_valid_membership_returns_context(self):
        mock_db = MagicMock(spec=Session)

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.lifecycle_state = "active"

        mock_membership = MagicMock()
        mock_membership.role = "admin"
        mock_membership.status = "active"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_tenant,
            mock_membership,
        ]

        validator = MembershipValidator()
        ctx = validator.validate_membership("user-1", "tenant-1", mock_db)

        assert ctx.tenant_id == "tenant-1"
        assert ctx.tenant_role == "admin"
        assert ctx.membership_status == "active"

    def test_tenant_not_found_raises(self):
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        validator = MembershipValidator()
        with pytest.raises(AuthError, match="Tenant not found"):
            validator.validate_membership("user-1", "nonexistent", mock_db)

    def test_suspended_tenant_raises(self):
        mock_db = MagicMock(spec=Session)

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-2"
        mock_tenant.lifecycle_state = "suspended"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        validator = MembershipValidator()
        with pytest.raises(AuthError, match="Tenant is suspended"):
            validator.validate_membership("user-1", "tenant-2", mock_db)

    def test_non_member_raises(self):
        mock_db = MagicMock(spec=Session)

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-3"
        mock_tenant.lifecycle_state = "active"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_tenant,
            None,  # no membership
        ]

        validator = MembershipValidator()
        with pytest.raises(AuthError, match="User is not a member of this tenant"):
            validator.validate_membership("user-1", "tenant-3", mock_db)

    def test_inactive_membership_raises(self):
        mock_db = MagicMock(spec=Session)

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-4"
        mock_tenant.lifecycle_state = "active"

        mock_membership = MagicMock()
        mock_membership.role = "member"
        mock_membership.status = "suspended"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_tenant,
            mock_membership,
        ]

        validator = MembershipValidator()
        with pytest.raises(AuthError, match="Membership is not active"):
            validator.validate_membership("user-1", "tenant-4", mock_db)

    def test_non_active_tenant_state_raises(self):
        mock_db = MagicMock(spec=Session)

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-5"
        mock_tenant.lifecycle_state = "archived"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_tenant

        validator = MembershipValidator()
        with pytest.raises(AuthError, match="Tenant is not active"):
            validator.validate_membership("user-1", "tenant-5", mock_db)
