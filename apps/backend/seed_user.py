"""One-off script to seed a login user into the control plane database."""

import os
import sys

# Ensure project root is on path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select

from auth.hashing import hash_password
from auth.schema import UserModel
from common.database import init_db, session_factory

EMAIL = "admin@canopy.dev"
PASSWORD = "admin123"
DISPLAY_NAME = "Admin User"


def main():
    init_db()
    session = session_factory()()
    try:
        existing = session.execute(select(UserModel).where(UserModel.email == EMAIL)).scalar_one_or_none()
        if existing:
            print(f"User already exists: {EMAIL}")
            return

        user = UserModel(
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            display_name=DISPLAY_NAME,
            is_active=True,
        )
        session.add(user)
        session.commit()
        print(f"Created user {EMAIL} / {PASSWORD}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
