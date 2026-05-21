from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from auth.domain import (
    LoginInput,
    LoginOutput,
    LoginOutputUser,
    SessionOutput,
    TenantInfo,
)
from auth.hashing import verify_password
from auth.repository import AuthRepository
from common.config import settings
from common.errors import AuthError
from context.membership_validator import MembershipValidator
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel

_TOKEN_EXPIRY_HOURS = 24
_ALGORITHM = "HS256"


def _create_token(
    user_id: str,
    tenant_id: str | None = None,
    impersonated: bool = False,
    admin_id: str | None = None,
    impersonation_session_id: str | None = None,
) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(hours=_TOKEN_EXPIRY_HOURS)
    payload = {"sub": user_id, "exp": expires_at}
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if impersonated:
        payload["impersonated"] = True
        payload["admin_id"] = admin_id
        payload["impersonation_session_id"] = impersonation_session_id
    token = jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)
    return token, expires_at


def _decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        return {
            "sub": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
            "impersonated": payload.get("impersonated", False),
            "admin_id": payload.get("admin_id"),
            "impersonation_session_id": payload.get("impersonation_session_id"),
        }
    except JWTError:
        return None


class AuthService:
    def __init__(self, db: Session):
        self._repo = AuthRepository(db)
        self._db = db

    def login(self, input_: LoginInput) -> LoginOutput:
        user = self._repo.find_by_email(input_.email)
        if user is None or not verify_password(input_.password, user.password_hash):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("Account is inactive")

        self._repo.update_login_timestamp(user)

        tenants = self.get_user_tenants(user.id)
        first_tenant_id = tenants[0]["tenant_id"] if tenants else None
        token, expires_at = _create_token(user.id, tenant_id=first_tenant_id)
        return LoginOutput(
            user=LoginOutputUser(id=user.id, email=user.email, display_name=user.display_name),
            token=token,
            expires_at=expires_at,
            tenants=[TenantInfo(**t) for t in tenants],
        )

    def get_user_tenants(self, user_id: str) -> list[dict]:
        memberships = (
            self._db.query(TenantMembershipModel)
            .filter(
                TenantMembershipModel.user_id == user_id,
                TenantMembershipModel.status == "active",
            )
            .all()
        )
        if not memberships:
            return []

        tenant_ids = [m.tenant_id for m in memberships]
        tenants = (
            self._db.query(TenantModel)
            .filter(
                TenantModel.id.in_(tenant_ids),
                TenantModel.lifecycle_state == "active",
            )
            .order_by(TenantModel.name)
            .all()
        )
        membership_map = {m.tenant_id: m for m in memberships}
        return [
            {
                "tenant_id": t.id,
                "tenant_name": t.name,
                "role": membership_map[t.id].role,
            }
            for t in tenants
            if t.id in membership_map
        ]

    def switch_tenant(self, user_id: str, tenant_id: str) -> str:
        validator = MembershipValidator()
        validator.validate_membership(user_id, tenant_id, self._db)
        token, _ = _create_token(user_id, tenant_id=tenant_id)
        return token

    def validate_session(self, token: str) -> SessionOutput:
        decoded = _decode_token(token)
        if decoded is None:
            return SessionOutput(authenticated=False)

        user_id = decoded["sub"]
        user = self._repo.find_by_id(user_id)
        if user is None or not user.is_active:
            return SessionOutput(authenticated=False)

        tenant_id = decoded.get("tenant_id")
        tenant_role = None
        if tenant_id:
            try:
                validator = MembershipValidator()
                ctx = validator.validate_membership(user_id, tenant_id, self._db)
                tenant_role = ctx.tenant_role
            except AuthError:
                tenant_id = None

        tenants = self.get_user_tenants(user_id)

        return SessionOutput(
            authenticated=True,
            user=LoginOutputUser(id=user.id, email=user.email, display_name=user.display_name),
            tenant_id=tenant_id,
            tenant_role=tenant_role,
            tenants=[TenantInfo(**t) for t in tenants],
        )

    def logout(self, token: str) -> None:
        pass
