"""Centralized authorization utilities for tenant-scoped access control.

All route-level tenant-enforcement and role-checking should go through
these functions rather than being reimplemented ad hoc in each handler.
"""

from common.errors import AuthError
from context.tenant_context import TenantContext

# ─── Role constants ───

ROLE_PLATFORM_ADMIN = "platform_admin"
ROLE_TENANT_ADMIN = "admin"
ROLE_TENANT_MEMBER = "member"


# ─── Role checks ───


def require_platform_admin(is_admin: bool) -> None:
    """Raise AuthError if the user is not a platform admin."""
    if not is_admin:
        raise AuthError("Platform admin access required")


def require_tenant_admin(ctx: TenantContext) -> None:
    """Raise AuthError if the user is not a tenant admin."""
    if ctx.tenant_role not in (ROLE_TENANT_ADMIN,):
        raise AuthError("Tenant admin access required")


def require_governance_actor(ctx: TenantContext, is_admin: bool) -> None:
    """Raise AuthError if the user is neither a platform admin nor tenant admin."""
    if not is_admin and ctx.tenant_role not in (ROLE_TENANT_ADMIN,):
        raise AuthError("Admin or governance access required")


def require_at_least_member(ctx: TenantContext) -> None:
    """Raise AuthError if the user does not have at least member-level access."""
    if ctx.tenant_role not in (ROLE_TENANT_ADMIN, ROLE_TENANT_MEMBER):
        raise AuthError("Tenant membership required")


# ─── Ownership verification ───


def verify_tenant_ownership(
    ctx: TenantContext,
    resource_tenant_id: str | None,
    resource_label: str = "Resource",
) -> None:
    """Raise AuthError if the resource does not belong to the request's tenant.

    Resources with no tenant_id are treated as cross-tenant (rejected).
    """
    if resource_tenant_id is None:
        raise AuthError(f"{resource_label} has no tenant ownership")
    if resource_tenant_id != ctx.tenant_id:
        raise AuthError(f"{resource_label} does not belong to the current tenant")


def resolve_tenant_context(ctx: TenantContext | None) -> str:
    """Resolve a tenant_id from context or raise.

    Must be used by all tenant-scoped routes so that cross-tenant
    access is rejected at a single enforcement point.
    """
    if ctx is None:
        raise AuthError("No tenant selected")
    return ctx.tenant_id
