"""Integration tests for computed property API (Issue 3)."""

import uuid

import pytest

from auth.hashing import hash_password
from auth.schema import UserModel
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_revision.domain import ComputedProperty, EntityProperty
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


class TestComputedPropertyApi:
    def test_add_computed_property(self, client, auth_headers, db_session):
        """POST /entities/{id}/draft/computed-properties adds a computed property."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="cp_api",
                display_name="CP API",
                description="CP API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            lock_holder_id="test-user-1",
        )

        payload = {
            "property_key": "total_comp",
            "display_name": "Total Compensation",
            "formula": "multiply(salary, 1.1)",
            "formula_type": "arithmetic",
            "output_type": "number",
            "sort_order": 1,
            "is_active": True,
        }

        response = client.post(
            f"/api/entities/{entity_id}/draft/computed-properties",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert len(data["computed_properties"]) == 1
        assert data["computed_properties"][0]["property_key"] == "total_comp"

    def test_update_computed_property_formula(self, client, auth_headers, db_session):
        """PUT /entities/{id}/draft/computed-properties/{id} updates formula."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="cp_update_api",
                display_name="CP Update API",
                description="CP Update API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="test-user-1",
        )

        payload = {
            "formula": "multiply(salary, 1.2)",
        }

        response = client.put(
            f"/api/entities/{entity_id}/draft/computed-properties/cp1",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["computed_properties"][0]["formula"] == "multiply(salary, 1.2)"

    def test_remove_computed_property(self, client, auth_headers, db_session):
        """DELETE /entities/{id}/draft/computed-properties/{id} removes it."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="cp_remove_api",
                display_name="CP Remove API",
                description="CP Remove API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="test-user-1",
        )

        response = client.delete(
            f"/api/entities/{entity_id}/draft/computed-properties/cp1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["computed_properties"]) == 0

    def test_list_computed_properties(self, client, auth_headers, db_session):
        """GET /entities/{id}/draft/computed-properties returns the list."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="cp_list_api",
                display_name="CP List API",
                description="CP List API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="test-user-1",
        )

        response = client.get(
            f"/api/entities/{entity_id}/draft/computed-properties",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["property_key"] == "total_comp"

    def test_syntax_error_blocks_add(self, client, auth_headers, db_session):
        """Adding a computed property with empty formula is rejected."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="cp_syntax_api",
                display_name="CP Syntax API",
                description="CP Syntax API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            lock_holder_id="test-user-1",
        )

        payload = {
            "property_key": "bad",
            "display_name": "Bad",
            "formula": "",
            "formula_type": "arithmetic",
            "output_type": "number",
            "sort_order": 1,
            "is_active": True,
        }

        response = client.post(
            f"/api/entities/{entity_id}/draft/computed-properties",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_publish_includes_computed_properties(self, client, auth_headers, db_session):
        """Published revision includes computed properties."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="cp_publish_api",
                display_name="CP Publish API",
                description="CP Publish API",
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="test-user-1",
        )

        response = client.post(
            f"/api/entities/{entity_id}/draft/publish",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert len(data["computed_properties"]) == 1
        assert data["computed_properties"][0]["property_key"] == "total_comp"
