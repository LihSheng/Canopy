"""Integration tests for binding recovery API (Issue 3)."""

import uuid

import pytest

from auth.hashing import hash_password
from auth.schema import UserModel
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_revision.domain import EntityProperty, SourceBinding
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def auth_headers(client, db_session):
    """Override conftest auth_headers to avoid stale session issues."""
    user = UserModel(
        id="test-user-1",
        email="admin@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(user)
    tenant = TenantModel(
        id="test-tenant-1",
        tenant_uuid="tuuid-test-1",
        name="Test Tenant",
        slug="test-tenant",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant)
    membership = TenantMembershipModel(
        user_id="test-user-1",
        tenant_id="test-tenant-1",
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestBindingRecoveryApi:
    def test_get_recovery_suggestions(self, client, auth_headers, db_session):
        """GET /entities/{id}/draft/bindings/recover returns suggestions."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="recover_api",
                display_name="Recover API",
                description="Recover API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[
                SourceBinding(property_key="name", source_node_id="sn1", source_field_name="old_name", is_active=True)
            ],
            source_nodes=[
                {
                    "source_id": "sn1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["name", "email"],
                }
            ],
            lock_holder_id="test-user-1",
        )

        response = client.get(
            f"/api/entities/{entity_id}/draft/bindings/recover",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "sn1" in data
        assert data["sn1"]["old_name"]["suggested_field"] == "name"
        assert data["sn1"]["old_name"]["confidence"] == "high"

    def test_apply_recovery_mapping(self, client, auth_headers, db_session):
        """PUT /entities/{id}/draft/bindings/recover applies suggestions."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="recover_apply_api",
                display_name="Recover Apply API",
                description="Recover Apply API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[
                SourceBinding(property_key="name", source_node_id="sn1", source_field_name="old_name", is_active=True)
            ],
            source_nodes=[
                {
                    "source_id": "sn1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["name", "email"],
                }
            ],
            lock_holder_id="test-user-1",
        )

        payload = {"sn1": {"old_name": "name"}}

        response = client.put(
            f"/api/entities/{entity_id}/draft/bindings/recover",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_bindings"][0]["source_field_name"] == "name"
