from datetime import UTC, datetime

from sqlalchemy.orm import Session

from auth.schema import UserModel


class AuthRepository:
    def __init__(self, db: Session):
        self._db = db

    def find_by_email(self, email: str) -> UserModel | None:
        return self._db.query(UserModel).filter(UserModel.email == email).first()

    def find_by_id(self, user_id: str) -> UserModel | None:
        return self._db.query(UserModel).filter(UserModel.id == user_id).first()

    def create(self, email: str, password_hash: str, display_name: str) -> UserModel:
        user = UserModel(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_login_timestamp(self, user: UserModel) -> None:
        user.last_login_at = datetime.now(UTC)
        self._db.commit()
