from dataclasses import asdict

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionResponse,
    SessionUser,
)
from auth.domain import LoginInput
from auth.service import AuthService
from common.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    result = service.login(LoginInput(email=body.email, password=body.password))
    response.set_cookie(
        key="herd_token",
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
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response) -> LogoutResponse:
    response.delete_cookie(key="herd_token")
    return LogoutResponse(message="Logged out")


@router.get("/session", response_model=SessionResponse)
def session(
    current_user: SessionUser = Depends(get_current_user),
) -> SessionResponse:
    return SessionResponse(authenticated=True, user=current_user)
