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


# ─── Entity Link Fixtures ───


@pytest.fixture
def seed_target_object_type(db_session, object_type_service, tenant_context):
    """Create a second object type to serve as link target."""
    obj = object_type_service.create(
        tenant_id=tenant_context.tenant_id,
        object_type_key="target_department",
        display_name="Target Department",
        description="A target object type for link tests",
    )
    return obj


@pytest.fixture
def seed_target_mapping(db_session, tenant_context, seed_target_object_type):
    """Create a mapping for the target object type so PK resolution works.

    Uses repository directly to avoid auth dependency.
    """
    import uuid
    from datetime import UTC, datetime

    from semantic.domain import PropertyMapping, SemanticMapping
    from semantic.repository import SemanticMappingRepository

    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="link-target-ds",
        dataset_version_id="link-target-v",
        version_number=1,
        object_type_id=seed_target_object_type.id,
        object_type_key=seed_target_object_type.object_type_key,
        properties=[
            PropertyMapping(
                source_column="id",
                property_name="id",
                semantic_type="string",
                included=True,
                is_primary_key=True,
            ),
            PropertyMapping(
                source_column="name",
                property_name="name",
                semantic_type="string",
                included=True,
                is_primary_key=False,
            ),
        ],
        created_at=datetime.now(UTC),
    )
    repo = SemanticMappingRepository(db_session)
    saved = repo.save(mapping)
    return saved


# ─── Link Validation API ───


class TestLinkValidationAPI:
    """Tests for link validation via the validate endpoint."""

    def test_validate_links_valid(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "dept_id",
                        "property_name": "dept_id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
                "links": [
                    {
                        "link_id": "dept_link",
                        "display_name": "Department Link",
                        "source_property_key": "dept_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_duplicate_link_id(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "dept_id",
                        "property_name": "dept_id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                    {
                        "source_column": "mgr_id",
                        "property_name": "mgr_id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
                "links": [
                    {
                        "link_id": "my_link",
                        "display_name": "First",
                        "source_property_key": "dept_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                    {
                        "link_id": "my_link",
                        "display_name": "Second",
                        "source_property_key": "mgr_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_fields = [e["field"] for e in data["errors"]]
        assert any("links[0].link_id" in f or "links[1].link_id" in f for f in error_fields)
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("duplicate" in m for m in error_messages)

    def test_validate_duplicate_edge(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "dept_id",
                        "property_name": "dept_id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
                "links": [
                    {
                        "link_id": "link_a",
                        "display_name": "Link A",
                        "source_property_key": "dept_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                    {
                        "link_id": "link_b",
                        "display_name": "Link B",
                        "source_property_key": "dept_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("duplicate edge" in m for m in error_messages)

    def test_validate_excluded_source_property(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "internal_code",
                        "property_name": "internal_code",
                        "semantic_type": "string",
                        "included": False,
                        "is_primary_key": False,
                    },
                ],
                "links": [
                    {
                        "link_id": "bad_link",
                        "display_name": "Bad Link",
                        "source_property_key": "internal_code",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("excluded" in m for m in error_messages)

    def test_validate_missing_target_pk(self, client, auth_headers, seed_object_type, seed_target_object_type):
        """Target object type has no mapping (no PK) — should get clear error."""
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "dept_id",
                        "property_name": "dept_id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
                "links": [
                    {
                        "link_id": "dept_link",
                        "display_name": "Department",
                        "source_property_key": "dept_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("primary key" in m for m in error_messages)


# ─── Link Persistence API ───


class TestLinkPersistenceAPI:
    """Tests for link persistence in mapping create/update/get."""

    def test_create_mapping_with_links(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        response = client.post(
            "/api/semantic/datasets/link-test-ds/versions/link-test-v/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                    {
                        "source_column": "dept_id",
                        "property_name": "dept_id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
                "links": [
                    {
                        "link_id": "dept_link",
                        "display_name": "Department Link",
                        "source_property_key": "dept_id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["links"]) == 1
        assert data["links"][0]["link_id"] == "dept_link"
        assert data["links"][0]["target_property_key"] == "id"  # resolved PK

    def test_get_mapping_returns_links(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        # Create
        create_resp = client.post(
            "/api/semantic/datasets/link-get-ds/versions/link-get-v/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
                "links": [
                    {
                        "link_id": "simple_link",
                        "display_name": "Simple",
                        "source_property_key": "id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_many",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201

        # Get
        get_resp = client.get(
            "/api/semantic/datasets/link-get-ds/versions/link-get-v/mapping",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert len(data["links"]) == 1
        assert data["links"][0]["link_id"] == "simple_link"
        assert data["links"][0]["cardinality"] == "many_to_many"

    def test_update_mapping_preserves_links(
        self, client, auth_headers, seed_object_type, seed_target_object_type, seed_target_mapping
    ):
        # Create initial
        client.post(
            "/api/semantic/datasets/link-upd-ds/versions/link-upd-v/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
                "links": [
                    {
                        "link_id": "link1",
                        "display_name": "Link One",
                        "source_property_key": "id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_one",
                    },
                ],
            },
            headers=auth_headers,
        )

        # Update with new links
        update_resp = client.put(
            "/api/semantic/datasets/link-upd-ds/versions/link-upd-v/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
                "links": [
                    {
                        "link_id": "link1",
                        "display_name": "Link One Updated",
                        "source_property_key": "id",
                        "target_object_type_id": seed_target_object_type.id,
                        "target_property_key": "id",
                        "cardinality": "many_to_many",
                    },
                ],
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["version_number"] == 2
        assert len(data["links"]) == 1
        assert data["links"][0]["display_name"] == "Link One Updated"
        assert data["links"][0]["cardinality"] == "many_to_many"

    def test_create_mapping_without_links_still_works(self, client, auth_headers, seed_object_type):
        """Backward compatibility: creating mapping without links field still works."""
        response = client.post(
            "/api/semantic/datasets/no-link-ds/versions/no-link-v/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "id",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["links"] == []


# ─── Mapping Persistence API ───


class TestMappingCRUDAPI:
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
