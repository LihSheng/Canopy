from auth.hashing import hash_password
from auth.repository import AuthRepository
from common.database import init_db, session_factory

DEFAULT_EMAIL = "admin@herd.example"
DEFAULT_PASSWORD = "admin123"
DEFAULT_DISPLAY_NAME = "Admin User"


def main() -> None:
    init_db()
    db = session_factory()()
    try:
        repo = AuthRepository(db)
        existing_user = repo.find_by_email(DEFAULT_EMAIL)
        if existing_user is not None:
            print(f"User already exists: {DEFAULT_EMAIL}")
            return

        repo.create(
            email=DEFAULT_EMAIL,
            password_hash=hash_password(DEFAULT_PASSWORD),
            display_name=DEFAULT_DISPLAY_NAME,
        )
        print(f"Seeded user: {DEFAULT_EMAIL}")
        print(f"Password: {DEFAULT_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
