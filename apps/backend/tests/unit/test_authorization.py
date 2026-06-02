"""Tests for centralized authorization utilities and tenant ownership enforcement.

Verifies:
- verify_tenant_ownership rejects cross-tenant access
- verify_tenant_ownership rejects null tenant_id
- resolve_tenant_context raises when no context
- Role checks raise appropriately
"""

import pytest

from common.errors import AuthError
from context.authorization import (
    require_at_least_member,
    require_governance_actor,
    require_platform_admin,
    require_tenant_admin,
    resolve_tenant_context,
    verify_tenant_ownership,
)
from context.tenant_context import TenantContext

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------


def _ctx(tenant_id: str = "tenant-1", role: str = "member") -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        tenant_role=role,
        membership_status="active",
        is_impersonated=False,
    )


# ---------------------------------------------------------------
# verify_tenant_ownership
# ---------------------------------------------------------------


class TestVerifyTenantOwnership:
    def test_matching_tenant_passes(self):
        ctx = _ctx("tenant-1")
        verify_tenant_ownership(ctx, "tenant-1")  # does not raise

    def test_different_tenant_raises(self):
        ctx = _ctx("tenant-1")
        with pytest.raises(AuthError, match="does not belong"):
            verify_tenant_ownership(ctx, "tenant-2")

    def test_null_tenant_id_raises(self):
        ctx = _ctx("tenant-1")
        with pytest.raises(AuthError, match="no tenant ownership"):
            verify_tenant_ownership(ctx, None)

    def test_custom_resource_label_in_message(self):
        ctx = _ctx("tenant-1")
        with pytest.raises(AuthError, match="MyConnection does not belong"):
            verify_tenant_ownership(ctx, "tenant-2", resource_label="MyConnection")


# ---------------------------------------------------------------
# resolve_tenant_context
# ---------------------------------------------------------------


class TestResolveTenantContext:
    def test_resolves_from_context(self):
        ctx = _ctx("tenant-1")
        assert resolve_tenant_context(ctx) == "tenant-1"

    def test_raises_when_no_context(self):
        with pytest.raises(AuthError, match="No tenant"):
            resolve_tenant_context(None)


# ---------------------------------------------------------------
# require_platform_admin
# ---------------------------------------------------------------


class TestRequirePlatformAdmin:
    def test_admin_passes(self):
        require_platform_admin(is_admin=True)  # does not raise

    def test_non_admin_raises(self):
        with pytest.raises(AuthError, match="Platform admin"):
            require_platform_admin(is_admin=False)


# ---------------------------------------------------------------
# require_tenant_admin
# ---------------------------------------------------------------


class TestRequireTenantAdmin:
    def test_tenant_admin_passes(self):
        ctx = _ctx(role="admin")
        require_tenant_admin(ctx)  # does not raise

    def test_member_raises(self):
        ctx = _ctx(role="member")
        with pytest.raises(AuthError, match="Tenant admin"):
            require_tenant_admin(ctx)


# ---------------------------------------------------------------
# require_governance_actor
# ---------------------------------------------------------------


class TestRequireGovernanceActor:
    def test_platform_admin_passes(self):
        ctx = _ctx(role="member")
        require_governance_actor(ctx, is_admin=True)  # does not raise

    def test_tenant_admin_passes(self):
        ctx = _ctx(role="admin")
        require_governance_actor(ctx, is_admin=False)  # does not raise

    def test_member_raises_when_not_admin(self):
        ctx = _ctx(role="member")
        with pytest.raises(AuthError, match="Admin or governance"):
            require_governance_actor(ctx, is_admin=False)


# ---------------------------------------------------------------
# require_at_least_member
# ---------------------------------------------------------------


class TestRequireAtLeastMember:
    def test_admin_passes(self):
        ctx = _ctx(role="admin")
        require_at_least_member(ctx)  # does not raise

    def test_member_passes(self):
        ctx = _ctx(role="member")
        require_at_least_member(ctx)  # does not raise

    def test_unknown_role_raises(self):
        ctx = _ctx(role="viewer")
        with pytest.raises(AuthError, match="membership"):
            require_at_least_member(ctx)
