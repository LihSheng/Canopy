"""Reset all application databases and recreate from ORM models.

Drops every table in the control-plane and tenant-data databases, then
recreates the full schema from the latest ORM model definitions. Finally
seeds the default admin user.

Usage:
    cd apps/backend
    python reset_db.py

PostgreSQL only.
"""

import os
import subprocess
import sys
from pathlib import Path

# Ensure the backend package root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

from auth.hashing import hash_password
from auth.schema import UserModel
from common.config import settings
from common.database import (
    init_db,
    reset_engine,
    session_factory,
)

# ── helpers ────────────────────────────────────────────────────────────────


def _drop_postgres_tables(database_url: str) -> None:
    """Drop everything in the public schema (tables, views, sequences, etc.)."""
    # Connect to the target database directly (not 'postgres')
    eng = create_engine(database_url)
    try:
        with eng.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            print(f"  Dropped and recreated public schema in {database_url}")
    finally:
        eng.dispose()


def _reset_database(database_url: str, label: str) -> None:
    """Reset one logical database by dropping and recreating the public schema."""
    if not database_url:
        print(f"[SKIP] {label}: no URL configured")
        return

    print(f"\n[{label}] {database_url}")
    _drop_postgres_tables(database_url)


# ── seed ────────────────────────────────────────────────────────────────────


def _seed_admin_user() -> None:
    from sqlalchemy import select

    session = session_factory()()
    try:
        existing = session.execute(select(UserModel).where(UserModel.email == "admin@canopy.dev")).scalar_one_or_none()
        if existing:
            print("  Admin user already exists — skipped")
            return
        user = UserModel(
            email="admin@canopy.dev",
            password_hash=hash_password("admin123"),
            display_name="Admin User",
            is_active=True,
        )
        session.add(user)
        session.commit()
        print("  Seeded admin user: admin@canopy.dev / admin123")
    finally:
        session.close()


# ── main ────────────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("  Canopy — Database Reset")
    print("=" * 60)

    # 1. Drop old databases
    _reset_database(settings.resolved_control_plane_database_url, "Control Plane")
    _reset_database(settings.resolved_tenant_data_database_url, "Tenant Data")

    # Flush cached engines so fresh connections target the new databases
    reset_engine()

    # 2. Recreate all tables from ORM models
    print("\n[CREATE] Running init_db() to recreate all tables...")
    init_db()
    print("  Tables created.")

    # 3. Stamp alembic head so migration tracking is aligned
    print("\n[ALEMBIC] Stamping head revision...")
    _backend_dir = Path(__file__).resolve().parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "stamp", "head"],
        cwd=str(_backend_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  Alembic stamped to head.")
    else:
        print(f"  Alembic stamp warning (non-fatal): {result.stderr.strip()}")

    # 4. Seed admin user
    print("\n[SEED] Creating default admin user...")
    _seed_admin_user()

    print("\nDone. Database rebuilt with latest ORM schema.")
    print("  Login: admin@canopy.dev / admin123")


if __name__ == "__main__":
    main()
