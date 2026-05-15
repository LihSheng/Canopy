from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from auth.domain import LoginInput, LoginOutput, LoginOutputUser, SessionOutput
from auth.hashing import verify_password
from auth.repository import AuthRepository
from common.config import settings
from common.errors import AuthError

_TOKEN_EXPIRY_HOURS = 24
_ALGORITHM = "HS256"


def _create_token(user_id: str) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(hours=_TOKEN_EXPIRY_HOURS)
    payload = {"sub": user_id, "exp": expires_at}
    token = jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)
    return token, expires_at


def _decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


class AuthService:
    def __init__(self, db: Session):
        self._repo = AuthRepository(db)

    def login(self, input_: LoginInput) -> LoginOutput:
        user = self._repo.find_by_email(input_.email)
        if user is None or not verify_password(input_.password, user.password_hash):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("Account is inactive")

        self._repo.update_login_timestamp(user)

        token, expires_at = _create_token(user.id)
        return LoginOutput(
            user=LoginOutputUser(id=user.id, email=user.email, display_name=user.display_name),
            token=token,
            expires_at=expires_at,
        )

    def validate_session(self, token: str) -> SessionOutput:
        user_id = _decode_token(token)
        if user_id is None:
            return SessionOutput(authenticated=False)

        user = self._repo.find_by_id(user_id)
        if user is None or not user.is_active:
            return SessionOutput(authenticated=False)

        return SessionOutput(
            authenticated=True,
            user=LoginOutputUser(id=user.id, email=user.email, display_name=user.display_name),
        )

    def logout(self, token: str) -> None:
        pass
