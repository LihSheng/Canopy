from dataclasses import asdict

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.schemas.auth import SessionUser
from auth.service import AuthService
from common.database import get_db
from common.errors import AuthError
from context.tenant_context import (
    TenantContext,
    get_current_tenant_context,
    reset_tenant_context,
    set_current_tenant_context,
)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> SessionUser:
    token: str | None = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        cookie_token = request.cookies.get("session_token")
        if cookie_token:
            token = cookie_token

    if token is None:
        raise AuthError("Not authenticated")

    service = AuthService(db)
    result = service.validate_session(token)
    if not result.authenticated or result.user is None:
        raise AuthError("Invalid or expired session")

    if result.tenant_id:
        ctx = TenantContext(
            tenant_id=result.tenant_id,
            tenant_role=result.tenant_role or "",
            membership_status="active",
            is_impersonated=False,
        )
        set_current_tenant_context(ctx)
    else:
        reset_tenant_context()

    request.state.tenant_session = result

    return SessionUser(**asdict(result.user))


async def get_tenant_context() -> TenantContext | None:
    return get_current_tenant_context()


async def require_tenant_context(
    user: SessionUser = Depends(get_current_user),
    ctx: TenantContext | None = Depends(get_tenant_context),
) -> TenantContext:
    if ctx is None:
        raise AuthError("No tenant selected")
    return ctx
