"""Integration tests for Semantic Mapping API."""

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
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
def seed_tenant_and_membership(db_session, seed_user):
    """Create a tenant and membership so auth tokens carry tenant context."""
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
        user_id=seed_user.id,
        tenant_id="test-tenant-1",
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    return tenant, membership


@pytest.fixture
def auth_headers(client, seed_user, seed_tenant_and_membership):
    """Override conftest auth_headers with a user that has a tenant membership."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_tenant_2_and_membership(db_session, seed_user):
    """Create a second tenant with membership for cross-tenant isolation tests."""
    tenant2 = TenantModel(
        id="test-tenant-2",
        tenant_uuid="tuuid-test-2",
        name="Tenant Two",
        slug="test-tenant-2",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant2)
    membership2 = TenantMembershipModel(
        user_id=seed_user.id,
        tenant_id="test-tenant-2",
        role="admin",
        status="active",
    )
    db_session.add(membership2)
    db_session.commit()
    return tenant2, membership2


@pytest.fixture
def auth_headers_tenant2(client, seed_user, seed_tenant_2_and_membership):
    """Auth headers for a user who belongs to tenant-2."""
    # Override tenant context to tenant-2 for the login to resolve correctly
    from context.tenant_context import set_current_tenant_context

    ctx2 = TenantContext(
        tenant_id="test-tenant-2",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx2)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]

    # Restore tenant-1 context
    ctx1 = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx1)

    return {"Authorization": f"Bearer {token}"}


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

    def test_list_object_types_no_tenant_returns_401(self, client, db_session):
        """Without tenant context, endpoints return 401."""
        # Create a user with no tenant membership and login
        from auth.hashing import hash_password
        from auth.schema import UserModel

        no_tenant_user = UserModel(
            id="no-tenant-user",
            email="noteam@canopy.dev",
            password_hash=hash_password("nopass"),
            display_name="No Tenant User",
            is_active=True,
        )
        db_session.add(no_tenant_user)
        db_session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"email": "noteam@canopy.dev", "password": "nopass"},
        )
        assert resp.status_code == 200
        no_tenant_token = resp.json()["token"]

        response = client.get(
            "/api/semantic/object-types",
            headers={"Authorization": f"Bearer {no_tenant_token}"},
        )
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
        assert response.status_code == 409  # Conflict, not 500

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

    # ─── Cross-tenant isolation ───

    def test_cross_tenant_get_returns_404(self, client, auth_headers_tenant2, tenant_context, seed_object_type):
        """Tenant-2 cannot read an object type owned by tenant-1."""
        response = client.get(
            f"/api/semantic/object-types/{seed_object_type.id}",
            headers=auth_headers_tenant2,
        )
        assert response.status_code == 404

    def test_cross_tenant_update_returns_404(self, client, auth_headers_tenant2, tenant_context, seed_object_type):
        """Tenant-2 cannot update an object type owned by tenant-1."""
        response = client.patch(
            f"/api/semantic/object-types/{seed_object_type.id}",
            json={"display_name": "Hacked"},
            headers=auth_headers_tenant2,
        )
        assert response.status_code == 404

    # ─── Duplicate key returns 409 ───

    def test_create_duplicate_key_returns_409(self, client, auth_headers, tenant_context, seed_object_type):
        """Duplicate object_type_key should return 409 Conflict, not 500."""
        response = client.post(
            "/api/semantic/object-types",
            json={
                "object_type_key": "test_employee",
                "display_name": "Another Employee",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409


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

    def test_schema_no_tenant_returns_401(self, client, db_session):
        from auth.hashing import hash_password
        from auth.schema import UserModel

        no_tenant_user = UserModel(
            id="no-tenant-schema-user",
            email="noschema@canopy.dev",
            password_hash=hash_password("nopass"),
            display_name="No Tenant User",
            is_active=True,
        )
        db_session.add(no_tenant_user)
        db_session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"email": "noschema@canopy.dev", "password": "nopass"},
        )
        assert resp.status_code == 200
        no_tenant_token = resp.json()["token"]

        response = client.get(
            "/api/semantic/datasets/fake-id/versions/fake-version/schema",
            headers={"Authorization": f"Bearer {no_tenant_token}"},
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

    # ─── P2: Validate must check object_type_id exists ───

    def test_validate_with_nonexistent_object_type(self, client, auth_headers):
        """Validate should fail when object_type_id doesn't exist."""
        response = client.post(
            "/api/semantic/datasets/test-ds/versions/test-version/mapping/validate",
            json={
                "object_type_id": "nonexistent-id",
                "object_type_key": "fake",
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
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("object type" in msg for msg in error_messages)

    def test_validate_with_cross_tenant_object_type(
        self, client, auth_headers_tenant2, tenant_context, seed_object_type
    ):
        """Validate should fail when object_type_id belongs to another tenant."""
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
            headers=auth_headers_tenant2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        error_messages = [e["message"].lower() for e in data["errors"]]
        assert any("object type" in msg for msg in error_messages)


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

    def test_create_mapping_derives_key_from_object_type(self, client, auth_headers, seed_object_type):
        """Server must derive object_type_key from the validated Object Type, not trust client input."""
        # Client sends a mismatched object_type_key
        response = client.post(
            "/api/semantic/datasets/test-ds-key/versions/test-v-key/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": "wrong_key_hacked",  # Client lied
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
        assert response.status_code == 201
        data = response.json()
        # Should use the Object Type's actual key, not the client-supplied one
        assert data["object_type_key"] == seed_object_type.object_type_key


# ─── P3: Object Type Primary Key Resolution ───


class TestObjectTypePrimaryKeyAPI:
    """Tests for object type primary key resolution endpoint."""

    def test_resolve_pk_returns_primary_key(self, client, auth_headers, seed_target_object_type, seed_target_mapping):
        """When object type has a mapping with PK, return the PK property name."""
        response = client.get(
            f"/api/semantic/object-types/{seed_target_object_type.id}/primary-key",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["property_name"] == "id"
        assert data["semantic_type"] == "string"

    def test_resolve_pk_returns_none_when_no_mapping(self, client, auth_headers, seed_object_type):
        """When object type has no mapping, return null PK."""
        response = client.get(
            f"/api/semantic/object-types/{seed_object_type.id}/primary-key",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["property_name"] is None

    def test_resolve_pk_not_found(self, client, auth_headers):
        """Non-existent object type returns 404."""
        response = client.get(
            "/api/semantic/object-types/nonexistent/primary-key",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ─── Computed Properties API ───


class TestComputedPropertiesAPI:
    """Integration tests for computed property creation, versioning, and coexistence."""

    def test_create_mapping_with_computed_property(self, client, auth_headers, seed_object_type):
        """Mapping can be created with computed_properties alongside ordinary properties."""
        response = client.post(
            "/api/semantic/datasets/cp-test-ds/versions/cp-test-v/mapping",
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
                "source_nodes": [
                    {
                        "source_id": "sn_emp",
                        "source_type": "dataset_table",
                        "name": "employees",
                        "reference_id": "ref_1",
                        "fields": ["first_name", "last_name"],
                    },
                ],
                "computed_properties": [
                    {
                        "id": "cp_full_name",
                        "property_name": "full_name",
                        "semantic_type": "string",
                        "composition_kind": "concat",
                        "expression": "{first} {last}",
                        "included": True,
                        "inputs": [
                            {"source_id": "sn_emp", "source_name": "employees", "field_name": "first_name"},
                            {"source_id": "sn_emp", "source_name": "employees", "field_name": "last_name"},
                        ],
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["version_number"] == 1
        assert len(data["properties"]) == 1
        assert len(data["computed_properties"]) == 1
        cp = data["computed_properties"][0]
        assert cp["id"] == "cp_full_name"
        assert cp["property_name"] == "full_name"
        assert cp["composition_kind"] == "concat"
        assert cp["expression"] == "{first} {last}"
        assert len(cp["inputs"]) == 2

    def test_computed_property_survives_versioned_update(self, client, auth_headers, seed_object_type):
        """Computed properties persist through versioned save/reload."""
        # Create v1
        create_resp = client.post(
            "/api/semantic/datasets/cp-vers-ds/versions/cp-vers-v/mapping",
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
                "source_nodes": [
                    {
                        "source_id": "sn_1",
                        "source_type": "dataset_table",
                        "name": "t1",
                        "reference_id": "r1",
                        "fields": ["col_a"],
                    },
                ],
                "computed_properties": [
                    {
                        "id": "cp_1",
                        "property_name": "region_label",
                        "semantic_type": "string",
                        "composition_kind": "lookup",
                        "expression": "",
                        "included": True,
                        "inputs": [
                            {"source_id": "sn_1", "source_name": "t1", "field_name": "col_a"},
                        ],
                    },
                ],
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        v1 = create_resp.json()
        assert v1["version_number"] == 1
        assert len(v1["computed_properties"]) == 1

        # Update (creates v2)
        update_resp = client.put(
            "/api/semantic/datasets/cp-vers-ds/versions/cp-vers-v/mapping",
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
                "source_nodes": [
                    {
                        "source_id": "sn_1",
                        "source_type": "dataset_table",
                        "name": "t1",
                        "reference_id": "r1",
                        "fields": ["col_a", "col_b"],
                    },
                ],
                "computed_properties": [
                    {
                        "id": "cp_1",
                        "property_name": "region_label",
                        "semantic_type": "string",
                        "composition_kind": "lookup",
                        "expression": "",
                        "included": True,
                        "inputs": [
                            {"source_id": "sn_1", "source_name": "t1", "field_name": "col_a"},
                        ],
                    },
                    {
                        "id": "cp_2",
                        "property_name": "plant_status",
                        "semantic_type": "string",
                        "composition_kind": "template",
                        "expression": "status: {col_b}",
                        "included": True,
                        "inputs": [
                            {"source_id": "sn_1", "source_name": "t1", "field_name": "col_b"},
                        ],
                    },
                ],
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        v2 = update_resp.json()
        assert v2["version_number"] == 2
        assert len(v2["computed_properties"]) == 2

        # Reload latest
        get_resp = client.get(
            "/api/semantic/datasets/cp-vers-ds/versions/cp-vers-v/mapping",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        latest = get_resp.json()
        assert latest["version_number"] == 2
        assert len(latest["computed_properties"]) == 2

    def test_computed_properties_coexist_with_ordinary_properties(self, client, auth_headers, seed_object_type):
        """Ordinary and computed properties can coexist in the same mapping."""
        response = client.post(
            "/api/semantic/datasets/cp-coexist-ds/versions/cp-coexist-v/mapping",
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
                        "source_column": "first_name",
                        "property_name": "first_name",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                    {
                        "source_column": "last_name",
                        "property_name": "last_name",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": False,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "sn_emp",
                        "source_type": "dataset_table",
                        "name": "employees",
                        "reference_id": "ref_1",
                        "fields": ["id", "first_name", "last_name"],
                    },
                ],
                "computed_properties": [
                    {
                        "id": "cp_full_name",
                        "property_name": "full_name",
                        "semantic_type": "string",
                        "composition_kind": "concat",
                        "expression": "{first} {last}",
                        "included": True,
                        "inputs": [
                            {"source_id": "sn_emp", "source_name": "employees", "field_name": "first_name"},
                            {"source_id": "sn_emp", "source_name": "employees", "field_name": "last_name"},
                        ],
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["properties"]) == 3
        assert len(data["computed_properties"]) == 1

    def test_computed_property_validation_empty_inputs_rejected(self, client, auth_headers, seed_object_type):
        """Computed properties with no inputs should be rejected."""
        response = client.post(
            "/api/semantic/datasets/cp-val-empty-ds/versions/cp-val-empty-v/mapping",
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
                "computed_properties": [
                    {
                        "id": "cp_bad",
                        "property_name": "bad_prop",
                        "semantic_type": "string",
                        "composition_kind": "concat",
                        "expression": "",
                        "included": True,
                        "inputs": [],
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_computed_property_duplicate_name_rejected(self, client, auth_headers, seed_object_type):
        """Computed property name conflicting with ordinary property should be rejected."""
        response = client.post(
            "/api/semantic/datasets/cp-val-dup-ds/versions/cp-val-dup-v/mapping",
            json={
                "object_type_id": seed_object_type.id,
                "object_type_key": seed_object_type.object_type_key,
                "properties": [
                    {
                        "source_column": "id",
                        "property_name": "full_name",
                        "semantic_type": "string",
                        "included": True,
                        "is_primary_key": True,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "sn_1",
                        "source_type": "dataset_table",
                        "name": "t1",
                        "reference_id": "r1",
                        "fields": ["col_a"],
                    },
                ],
                "computed_properties": [
                    {
                        "id": "cp_dup",
                        "property_name": "full_name",
                        "semantic_type": "string",
                        "composition_kind": "concat",
                        "expression": "",
                        "included": True,
                        "inputs": [
                            {"source_id": "sn_1", "source_name": "t1", "field_name": "col_a"},
                        ],
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_mapping_without_computed_properties_still_works(self, client, auth_headers, seed_object_type):
        """Backward compatibility: creating mapping without computed_properties still works."""
        response = client.post(
            "/api/semantic/datasets/no-cp-ds/versions/no-cp-v/mapping",
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
        assert response.status_code == 201
        data = response.json()
        assert data["computed_properties"] == []
