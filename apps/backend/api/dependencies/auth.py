from dataclasses import asdict

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.schemas.auth import SessionUser
from auth.service import AuthService
from common.database import get_db
from common.errors import AuthError

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
        cookie_token = request.cookies.get("herd_token")
        if cookie_token:
            token = cookie_token

    if token is None:
        raise AuthError("Not authenticated")

    service = AuthService(db)
    result = service.validate_session(token)
    if not result.authenticated or result.user is None:
        raise AuthError("Invalid or expired session")

    return SessionUser(**asdict(result.user))
