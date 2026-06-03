"""Seed a demo tenant and membership for the local admin login."""

import os
import sys

# Ensure backend root is on path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.repository import AuthRepository
from common.database import init_db, session_factory
from control_plane.membership_repository import MembershipRepository
from control_plane.tenant_repository import TenantRepository

DEFAULT_EMAIL = "admin@canopy.dev"
DEFAULT_TENANT_NAME = "Canopy Demo"
DEFAULT_TENANT_SLUG = "canopy-demo"
DEFAULT_ROLE = "admin"


def main() -> None:
    init_db()
    db = session_factory()()
    try:
        auth_repo = AuthRepository(db)
        tenant_repo = TenantRepository(db)
        membership_repo = MembershipRepository(db)

        user = auth_repo.find_by_email(DEFAULT_EMAIL)
        if user is None:
            raise RuntimeError(f"Missing user: {DEFAULT_EMAIL}. Run seed_demo_user.py first.")

        tenant = tenant_repo.get_tenant_by_slug(DEFAULT_TENANT_SLUG)
        if tenant is None:
            tenant = tenant_repo.create_tenant(name=DEFAULT_TENANT_NAME, slug=DEFAULT_TENANT_SLUG)
            tenant.lifecycle_state = "active"
            tenant.status = "active"
            db.commit()
            db.refresh(tenant)
            print(f"Created tenant: {tenant.name} ({tenant.id})")
        else:
            print(f"Tenant already exists: {tenant.name} ({tenant.id})")

        membership = membership_repo.get_membership(user.id, tenant.id)
        if membership is None:
            membership_repo.add_member(user.id, tenant.id, role=DEFAULT_ROLE)
            print(f"Added membership: {DEFAULT_EMAIL} -> {tenant.name} ({DEFAULT_ROLE})")
        else:
            if membership.status != "active" or membership.role != DEFAULT_ROLE:
                membership.status = "active"
                membership.role = DEFAULT_ROLE
                db.commit()
            print(f"Membership already exists: {DEFAULT_EMAIL} -> {tenant.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
