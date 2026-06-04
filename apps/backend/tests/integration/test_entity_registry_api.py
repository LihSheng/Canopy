"""Integration tests for Entity Registry API (GET /api/entities)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from dataset.schema import DatasetModel, DatasetVersionModel
from semantic.domain import PropertyMapping, SemanticMapping
from semantic.repository import ObjectTypeRepository, SemanticMappingRepository
from semantic.service import ObjectTypeService

pytestmark = pytest.mark.api_schema


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def tenant_context():
    """Activate a tenant context for all entity-registry API tests."""
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
def object_type_service(db_session):
    return ObjectTypeService(ObjectTypeRepository(db_session))


@pytest.fixture
def seed_entity(db_session, object_type_service, tenant_context):
    """Create an object type (entity) for registry tests."""
    return object_type_service.create(
        tenant_id=tenant_context.tenant_id,
        object_type_key="registry_test_employee",
        display_name="Registry Test Employee",
        description="Entity created for registry API tests",
    )


@pytest.fixture
def seed_entity_with_mapping(db_session, tenant_context, seed_entity):
    """Create an entity + a semantic mapping so the entity appears in the registry."""
    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="entity-registry-ds",
        dataset_version_id="entity-registry-v1",
        version_number=1,
        object_type_id=seed_entity.id,
        object_type_key=seed_entity.object_type_key,
        properties=[
            PropertyMapping(
                source_column="id",
                property_name="id",
                semantic_type="integer",
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
            PropertyMapping(
                source_column="deleted_at",
                property_name="deleted_at",
                semantic_type="datetime",
                included=False,
                is_primary_key=False,
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
    return seed_entity, saved


@pytest.fixture
def seed_entity_with_legacy_and_tenant_mappings(db_session, tenant_context, seed_entity):
    """Create legacy and tenant-owned mappings for the same entity."""
    legacy_dataset = DatasetModel(
        id="legacy-leave-dataset",
        tenant_id=None,
        project_id="default",
        connection_id="legacy-connection",
        name="org_leave_group",
        source_object_name="leave",
        status="active",
    )
    tenant_dataset = DatasetModel(
        id="tenant-leave-dataset",
        tenant_id=tenant_context.tenant_id,
        project_id="default",
        connection_id="tenant-connection",
        name="lv_emp_leave_request_file",
        source_object_name="leave",
        status="active",
    )
    db_session.add_all([legacy_dataset, tenant_dataset])

    db_session.add_all(
        [
            DatasetVersionModel(
                id="legacy-leave-version",
                dataset_id=legacy_dataset.id,
                run_id=None,
                version_number=1,
                status="ready",
                row_count=0,
                column_count=0,
                storage_path="legacy-path",
                raw_storage_path="legacy-raw-path",
            ),
            DatasetVersionModel(
                id="tenant-leave-version",
                dataset_id=tenant_dataset.id,
                run_id=None,
                version_number=1,
                status="ready",
                row_count=0,
                column_count=0,
                storage_path="tenant-path",
                raw_storage_path="tenant-raw-path",
            ),
        ]
    )
    db_session.commit()

    legacy_mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id=legacy_dataset.id,
        dataset_version_id="legacy-leave-version",
        version_number=3,
        object_type_id=seed_entity.id,
        object_type_key=seed_entity.object_type_key,
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
    tenant_mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id=tenant_dataset.id,
        dataset_version_id="tenant-leave-version",
        version_number=1,
        object_type_id=seed_entity.id,
        object_type_key=seed_entity.object_type_key,
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
    repo.save(legacy_mapping)
    repo.save(tenant_mapping)
    return seed_entity, legacy_dataset, tenant_dataset, legacy_mapping, tenant_mapping


# ─── Tests ────────────────────────────────────────────────────────────────────


class TestListEntities:
    def test_list_entities_empty(self, client, auth_headers):
        """Return empty list when no entities exist (but object type may exist)."""
        response = client.get("/api/entities", headers=auth_headers)
        assert response.status_code == 200
        # May be empty or may have objects without mappings
        assert isinstance(response.json(), list)

    def test_list_entities_includes_seeded(self, client, auth_headers, seed_entity_with_mapping):
        """List returns the seeded entity with correct metadata."""
        entity, mapping = seed_entity_with_mapping

        response = client.get("/api/entities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        item = next((r for r in data if r["id"] == entity.id), None)
        assert item is not None, f"Entity {entity.id} not found in registry list"
        assert item["display_name"] == entity.display_name
        assert item["object_type_key"] == entity.object_type_key
        assert item["description"] == entity.description
        assert item["dataset_id"] == mapping.dataset_id
        assert item["mapping_version"] == 1
        assert item["property_count"] == 3
        assert item["link_count"] == 0
        assert item["computed_property_count"] == 0

    def test_list_entities_search_by_name(self, client, auth_headers, seed_entity_with_mapping):
        """Search by display_name returns matching entities."""
        entity, _ = seed_entity_with_mapping

        response = client.get("/api/entities?q=Registry+Test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(r["id"] == entity.id for r in data)

    def test_list_entities_search_by_key(self, client, auth_headers, seed_entity_with_mapping):
        """Search by object_type_key returns matching entities."""
        entity, _ = seed_entity_with_mapping

        response = client.get("/api/entities?q=registry_test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(r["id"] == entity.id for r in data)

    def test_list_entities_search_no_match(self, client, auth_headers, seed_entity_with_mapping):
        """Search with no match returns empty list."""
        response = client.get("/api/entities?q=nonexistent_xyz_123", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_entities_requires_auth(self, client):
        """Unauthenticated request returns 401."""
        response = client.get("/api/entities")
        assert response.status_code == 401


class TestGetEntity:
    def test_get_entity_detail(self, client, auth_headers, seed_entity_with_mapping):
        """GET /api/entities/{id} returns full detail with mapping."""
        entity, mapping = seed_entity_with_mapping

        response = client.get(f"/api/entities/{entity.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entity.id
        assert data["display_name"] == entity.display_name
        assert data["object_type_key"] == entity.object_type_key
        assert data["description"] == entity.description
        assert data["mapping"] is not None
        assert data["mapping"]["id"] == mapping.id
        assert data["mapping"]["version_number"] == 1
        assert len(data["mapping"]["properties"]) == 3

        # Verify property details
        props = {p["property_name"]: p for p in data["mapping"]["properties"]}
        assert props["id"]["semantic_type"] == "integer"
        assert props["id"]["is_primary_key"] is True
        assert props["id"]["included"] is True
        assert props["deleted_at"]["included"] is False

    def test_get_entity_prefers_tenant_owned_dataset_over_legacy(
        self, client, auth_headers, seed_entity_with_legacy_and_tenant_mappings
    ):
        """Detail should resolve the tenant-owned backing dataset when both exist."""
        (
            entity,
            legacy_dataset,
            tenant_dataset,
            legacy_mapping,
            tenant_mapping,
        ) = seed_entity_with_legacy_and_tenant_mappings

        response = client.get(f"/api/entities/{entity.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert data["dataset_id"] == tenant_dataset.id
        assert data["dataset_name"] == tenant_dataset.name
        assert data["mapping"]["dataset_id"] == tenant_dataset.id
        assert data["mapping"]["version_number"] == tenant_mapping.version_number
        assert data["mapping"]["version_number"] != legacy_mapping.version_number

    def test_list_entities_prefers_tenant_owned_dataset_over_legacy(
        self, client, auth_headers, seed_entity_with_legacy_and_tenant_mappings
    ):
        """Registry list should show the tenant-owned dataset when both exist."""
        (
            entity,
            legacy_dataset,
            tenant_dataset,
            legacy_mapping,
            tenant_mapping,
        ) = seed_entity_with_legacy_and_tenant_mappings

        response = client.get("/api/entities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        item = next((r for r in data if r["id"] == entity.id), None)
        assert item is not None
        assert item["dataset_id"] == tenant_dataset.id
        assert item["dataset_name"] == tenant_dataset.name
        assert item["mapping_version"] == tenant_mapping.version_number
        assert item["mapping_version"] != legacy_mapping.version_number

    def test_get_entity_not_found(self, client, auth_headers):
        """Non-existent entity returns 404."""
        response = client.get("/api/entities/nonexistent-entity-id", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_entity_requires_auth(self, client, seed_entity_with_mapping):
        """Unauthenticated detail request returns 401."""
        entity, _ = seed_entity_with_mapping
        response = client.get(f"/api/entities/{entity.id}")
        assert response.status_code == 401


class TestEntityCrossTenantIsolation:
    """Verify entities from tenant-2 are not visible to tenant-1."""

    @pytest.fixture
    def seed_tenant_2_and_membership(self, db_session, seed_user):
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
    def auth_headers_tenant2(self, client, seed_user, seed_tenant_2_and_membership):
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

    def test_tenant2_entity_hidden_from_tenant1(
        self,
        client,
        auth_headers,
        auth_headers_tenant2,
        db_session,
        seed_entity_with_mapping,
    ):
        """Entity created in tenant-1 is not visible in tenant-2 and vice-versa."""
        entity_t1, _ = seed_entity_with_mapping

        # Create an entity in tenant-2
        from semantic.schema import ObjectTypeModel

        t2_entity = ObjectTypeModel(
            id=str(uuid.uuid4()),
            tenant_id="test-tenant-2",
            object_type_key="t2_only",
            display_name="T2 Only Entity",
            description="Only belongs to tenant-2",
        )
        db_session.add(t2_entity)
        db_session.commit()

        # Tenant-1 sees its own entity, not tenant-2's
        resp_t1 = client.get("/api/entities", headers=auth_headers)
        assert resp_t1.status_code == 200
        t1_ids = {r["id"] for r in resp_t1.json()}
        assert entity_t1.id in t1_ids
        assert t2_entity.id not in t1_ids

        # Tenant-2 sees its own entity, not tenant-1's
        resp_t2 = client.get("/api/entities", headers=auth_headers_tenant2)
        assert resp_t2.status_code == 200
        t2_ids = {r["id"] for r in resp_t2.json()}
        assert t2_entity.id in t2_ids
        assert entity_t1.id not in t2_ids
