from sqlalchemy.orm import Session

from common.errors import AuthError
from context.tenant_context import TenantContext
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel


class MembershipValidator:
    def validate_membership(self, user_id: str, tenant_id: str, db_session: Session) -> TenantContext:
        tenant = db_session.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if tenant is None:
            raise AuthError("Tenant not found")
        if tenant.lifecycle_state == "suspended":
            raise AuthError("Tenant is suspended")
        if tenant.lifecycle_state not in ("active",):
            raise AuthError(f"Tenant is not active (state: {tenant.lifecycle_state})")

        membership = (
            db_session.query(TenantMembershipModel)
            .filter(
                TenantMembershipModel.user_id == user_id,
                TenantMembershipModel.tenant_id == tenant_id,
            )
            .first()
        )
        if membership is None:
            raise AuthError("User is not a member of this tenant")
        if membership.status != "active":
            raise AuthError("Membership is not active")

        return TenantContext(
            tenant_id=tenant_id,
            tenant_role=membership.role,
            membership_status=membership.status,
            is_impersonated=False,
            database_target_ref=None,
            active_token_id=None,
        )
