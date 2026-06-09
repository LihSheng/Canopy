"""Integration tests for entity registry search (Issue 6, Step 7).

Verifies search by name, key, and deprecated filtering.
"""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.api_schema


@pytest.fixture(autouse=True)
def tenant_context():
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    yield ctx


@pytest.fixture
def seed_tenant_and_membership(db_session, seed_user):
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
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="search_test_entity",
        display_name="Search Test Entity",
        description="Entity for search tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_deprecated_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="deprecated_search_entity",
        display_name="Deprecated Search Entity",
        description="This entity is deprecated",
        status="deprecated",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_mapping_for_deprecated(db_session, tenant_context, seed_deprecated_entity):
    from semantic.domain import PropertyMapping, SemanticMapping
    from semantic.repository import SemanticMappingRepository

    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="deprecated-search-ds",
        dataset_version_id="deprecated-search-v1",
        version_number=1,
        object_type_id=seed_deprecated_entity.id,
        object_type_key=seed_deprecated_entity.object_type_key,
        properties=[
            PropertyMapping(
                source_column="id",
                property_name="id",
                semantic_type="integer",
                included=True,
                is_primary_key=True,
            ),
        ],
        links=[],
        computed_properties=[],
        source_nodes=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo = SemanticMappingRepository(db_session)
    saved = repo.save(mapping)
    return saved


class TestEntityRegistrySearch:
    def test_search_by_display_name(self, client, auth_headers, seed_entity):
        """GET /api/entities?q=... searches by display_name substring."""
        response = client.get("/api/entities?q=Search", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(seed_entity.display_name in item["display_name"] for item in data)

    def test_search_by_object_type_key(self, client, auth_headers, seed_entity):
        """GET /api/entities?q=... searches by object_type_key exact match."""
        response = client.get(f"/api/entities?q={seed_entity.object_type_key}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(item["object_type_key"] == seed_entity.object_type_key for item in data)

    def test_search_by_object_type_key_prefix(self, client, auth_headers, seed_entity):
        """GET /api/entities?q=... searches by object_type_key prefix."""
        response = client.get("/api/entities?q=search_test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(item["object_type_key"] == seed_entity.object_type_key for item in data)

    def test_search_excludes_deprecated_by_default(
        self, client, auth_headers, seed_deprecated_entity, seed_mapping_for_deprecated
    ):
        """GET /api/entities?q=... excludes deprecated entities by default."""
        response = client.get("/api/entities?q=deprecated", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert not any(item["id"] == seed_deprecated_entity.id for item in data)

    def test_search_include_deprecated(self, client, auth_headers, seed_deprecated_entity, seed_mapping_for_deprecated):
        """GET /api/entities?q=...&include_deprecated=true includes deprecated entities."""
        response = client.get("/api/entities?q=deprecated&include_deprecated=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(item["id"] == seed_deprecated_entity.id for item in data)

    def test_search_no_results_returns_empty_list(self, client, auth_headers):
        """GET /api/entities?q=nonexistent returns empty list."""
        response = client.get("/api/entities?q=nonexistent_xyz", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data == []
