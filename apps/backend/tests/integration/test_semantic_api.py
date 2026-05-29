"""Integration tests for Semantic Mapping API."""

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from semantic.repository import ObjectTypeRepository
from semantic.service import ObjectTypeService

pytestmark = pytest.mark.api_schema


# ─── Auto-use fixture: activate tenant context for every test ───


@pytest.fixture(autouse=True)
def tenant_context():
    """Set up and activate a tenant context for all semantic API tests."""
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    yield ctx
    # No cleanup needed — _setup_db resets engine each test


@pytest.fixture
def object_type_service(db_session):
    return ObjectTypeService(ObjectTypeRepository(db_session))


@pytest.fixture
def seed_object_type(db_session, object_type_service, tenant_context):
    """Create a reusable object type for mapping tests."""
    obj = object_type_service.create(
        tenant_id=tenant_context.tenant_id,
        object_type_key="test_employee",
        display_name="Test Employee",
        description="A test object type",
    )
    return obj


# ─── Object Type API ───


class TestObjectTypesAPI:
    """Tests for Object Type CRUD endpoints."""

    def test_list_object_types_no_tenant_returns_401(self, client, auth_headers):
        """Without tenant context, endpoints return 401."""
        # Clear tenant context to simulate missing-tenant scenario
        from context.tenant_context import reset_tenant_context

        reset_tenant_context()
        response = client.get("/api/semantic/object-types", headers=auth_headers)
        assert response.status_code == 401

    def test_create_object_type(self, client, auth_headers, tenant_context):
        response = client.post(
            "/api/semantic/object-types",
            json={
                "object_type_key": "new_type",
                "display_name": "New Type",
                "description": "A new object type",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["object_type_key"] == "new_type"
        assert data["display_name"] == "New Type"
        assert data["tenant_id"] == tenant_context.tenant_id
        assert "id" in data

    def test_create_duplicate_key_fails(self, client, auth_headers, tenant_context, seed_object_type):
        response = client.post(
            "/api/semantic/object-types",
            json={
                "object_type_key": "test_employee",
                "display_name": "Another",
            },
            headers=auth_headers,
        )
        assert response.status_code == 500  # Integrity error

    def test_get_object_type(self, client, auth_headers, tenant_context, seed_object_type):
        response = client.get(
            f"/api/semantic/object-types/{seed_object_type.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["id"] == seed_object_type.id

    def test_get_object_type_not_found(self, client, auth_headers):
        response = client.get(
            "/api/semantic/object-types/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_object_type(self, client, auth_headers, tenant_context, seed_object_type):
        response = client.patch(
            f"/api/semantic/object-types/{seed_object_type.id}",
            json={"display_name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "Updated Name"


# ─── Schema API ───


class TestSchemaAPI:
    """Tests for dataset version schema endpoint."""

    def test_schema_for_nonexistent_dataset(self, client, auth_headers):
        response = client.get(
            "/api/semantic/datasets/fake-id/versions/fake-version/schema",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_schema_no_tenant_returns_401(self, client, auth_headers):
        from context.tenant_context import reset_tenant_context

        reset_tenant_context()
        response = client.get(
            "/api/semantic/datasets/fake-id/versions/fake-version/schema",
            headers=auth_headers,
        )
        assert response.status_code == 401


# ─── Mapping Validation API ───


class TestMappingValidationAPI:
    """Tests for mapping validation endpoint."""

    def test_validate_valid_mapping(self, client, auth_headers, seed_object_type):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "col_a",
                        "property_name": "Column A",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert isinstance(data["errors"], list)

    def test_validate_missing_pk(self, client, auth_headers, seed_object_type):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "col_a",
                        "property_name": "Column A",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("primary key" in msg for msg in error_messages)

    def test_validate_duplicate_property_names(self, client, auth_headers, seed_object_type):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "col_a",
                        "property_name": "Same Name",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "col_b",
                        "property_name": "same name",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("duplicate" in msg for msg in error_messages)


# ─── Mapping Persistence API ───


class TestMappingCRUDAPI:
    """Tests for mapping creation and retrieval."""

    def test_create_and_get_mapping_happy_path(self, client, auth_headers, seed_object_type):
        # Create
        create_resp = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "ID",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "name",
                        "property_name": "Name",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["version_number"] == 1
        assert created["object_type_key"] == seed_object_type.object_type_key
        assert created["tenant_id"] == "test-tenant-1"
        assert len(created["properties"]) == 2

        # Get
        get_resp = client.get(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        assert fetched["id"] == created["id"]
        assert fetched["version_number"] == 1

    def test_update_creates_new_version(self, client, auth_headers, seed_object_type):
        # Create initial
        client.post(
            "/api/semantic/datasets/test-ds-2/versions/test-v2/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "ID",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
            },
            headers=auth_headers,
        )

        # Update (PUT creates new version)
        update_resp = client.put(
            "/api/semantic/datasets/test-ds-2/versions/test-v2/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "ID",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "new_col",
                        "property_name": "New Column",
                        "semantic_type": "integer",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["version_number"] == 2
        assert len(updated["properties"]) == 2

    def test_get_mapping_nonexistent(self, client, auth_headers):
        response = client.get(
            "/api/semantic/datasets/no-ds/versions/no-v/mapping",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() is None
