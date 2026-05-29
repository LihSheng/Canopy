from dataclasses import asdict

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionResponse,
    SessionUser,
    SwitchTenantRequest,
    TenantContextResponse,
    TenantInfo,
)
from auth.domain import LoginInput
from auth.service import AuthService
from common.database import get_db
from context.tenant_context import (
    TenantContext,
    get_current_tenant_context,
    set_current_tenant_context,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
_SESSION_COOKIE_NAME = "session_token"


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    result = service.login(LoginInput(email=body.email, password=body.password))
    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=result.token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
    )
    return {
        "user": asdict(result.user),
        "token": result.token,
        "expires_at": result.expires_at,
        "tenants": [{"tenant_id": t.tenant_id, "name": t.tenant_name, "role": t.role} for t in result.tenants],
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response) -> LogoutResponse:
    response.delete_cookie(key=_SESSION_COOKIE_NAME)
    return LogoutResponse(message="Logged out")


@router.get("/session", response_model=SessionResponse)
def session(
    request: Request,
    current_user: SessionUser = Depends(get_current_user),
) -> SessionResponse:
    ctx = get_current_tenant_context()
    session_data = getattr(request.state, "tenant_session", None)
    tenants: list[TenantInfo] = []
    if session_data is not None:
        tenants = [TenantInfo(tenant_id=t.tenant_id, name=t.tenant_name, role=t.role) for t in session_data.tenants]
    return SessionResponse(
        authenticated=True,
        user=current_user,
        tenant=TenantContextResponse(tenant_id=ctx.tenant_id, role=ctx.tenant_role) if ctx else None,
        tenants=tenants,
    )


@router.post("/switch-tenant", response_model=SessionResponse)
def switch_tenant(
    body: SwitchTenantRequest,
    request: Request,
    response: Response,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    service = AuthService(db)
    new_token = service.switch_tenant(current_user.id, body.tenant_id)
    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=new_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
    )
    session_result = service.validate_session(new_token)
    if session_result.tenant_id:
        ctx = TenantContext(
            tenant_id=session_result.tenant_id,
            tenant_role=session_result.tenant_role or "",
            membership_status="active",
            is_impersonated=False,
        )
        set_current_tenant_context(ctx)
    return {
        "authenticated": session_result.authenticated,
        "user": (
            {
                "id": session_result.user.id,
                "email": session_result.user.email,
                "display_name": session_result.user.display_name,
                "is_admin": session_result.user.is_admin,
            }
            if session_result.user
            else None
        ),
        "tenant": {
            "tenant_id": session_result.tenant_id,
            "role": session_result.tenant_role,
        }
        if session_result.tenant_id
        else None,
        "tenants": [{"tenant_id": t.tenant_id, "name": t.tenant_name, "role": t.role} for t in session_result.tenants],
        "token": new_token,
    }
