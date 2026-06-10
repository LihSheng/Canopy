"""Integration tests for enhanced entity detail API (Issue 6, Step 5).

Tests field_groups, materialized_preview, link_status, computed_property_warnings,
registry search, and deprecated entity filtering.
"""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import (
    ComputedProperty,
    EntityLink,
    EntityProperty,
    EntityRevision,
    RevisionStatus,
)
from entity_revision.repository import EntityRevisionRepository
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.api_schema


# ─── Fixtures ────────────────────────────────────────────────────────────────


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
    """Create a bare object type for detail tests."""
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="detail_test_entity",
        display_name="Detail Test Entity",
        description="Entity for detail API tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_revision_with_computed(db_session, tenant_context, seed_entity):
    """Create a published revision with base and computed properties."""
    now = datetime.now(UTC)
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=1,
        status=RevisionStatus.PUBLISHED.value,
        properties=[
            EntityProperty(
                property_id="prop-001",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=True,
                is_primary_key=False,
                sort_order=1,
            ),
        ],
        source_nodes=[
            {
                "source_id": "src-1",
                "source_type": "dataset_table",
                "name": "employees_csv",
                "reference_id": "ds-ref-1",
                "fields": ["salary"],
            }
        ],
        computed_properties=[
            ComputedProperty(
                id="cp-001",
                property_key="total_comp",
                display_name="Total Compensation",
                formula="salary * 1.1",
                formula_type="arithmetic",
                output_type="number",
                sort_order=1,
                is_active=True,
            ),
        ],
        layout_state={},
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    return repo.save(revision)


@pytest.fixture
def seed_draft_with_computed_warnings(db_session, tenant_context, seed_entity):
    """Create a draft revision with a computed property referencing a missing property."""
    now = datetime.now(UTC)
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=2,
        status=RevisionStatus.DRAFT.value,
        properties=[
            EntityProperty(
                property_id="prop-001",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=True,
                is_primary_key=False,
                sort_order=1,
            ),
        ],
        computed_properties=[
            ComputedProperty(
                id="cp-001",
                property_key="total_comp",
                display_name="Total Compensation",
                formula="multiply(missing_prop, 1.1)",
                formula_type="arithmetic",
                output_type="number",
                sort_order=1,
                is_active=True,
            ),
        ],
        layout_state={},
        lock_holder_id="user-1",
        locked_at=now,
        created_at=now,
        updated_at=now,
    )
    return repo.save(revision)


@pytest.fixture
def seed_target_entity(db_session, tenant_context):
    """Create a target entity for link resolution tests."""
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="target_dept",
        display_name="Target Department",
        description="Target entity for link tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_target_published(db_session, tenant_context, seed_target_entity):
    """Create a published revision for the target entity."""
    now = datetime.now(UTC)
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_target_entity.id,
        revision_number=1,
        status=RevisionStatus.PUBLISHED.value,
        properties=[
            EntityProperty(
                property_id="prop-dept",
                property_key="dept_id",
                display_name="Department ID",
                semantic_type="string",
                is_required=True,
                is_primary_key=True,
                sort_order=1,
            ),
        ],
        layout_state={},
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    return repo.save(revision)


@pytest.fixture
def seed_published_with_link(db_session, tenant_context, seed_entity, seed_target_entity, seed_target_published):
    """Create a published revision with a link to the target entity."""
    now = datetime.now(UTC)
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=1,
        status=RevisionStatus.PUBLISHED.value,
        properties=[
            EntityProperty(
                property_id="prop-001",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=True,
                is_primary_key=False,
                sort_order=1,
            ),
            EntityProperty(
                property_id="prop-002",
                property_key="dept_id",
                display_name="Department ID",
                semantic_type="string",
                is_required=False,
                is_primary_key=False,
                sort_order=2,
            ),
        ],
        links=[
            EntityLink(
                link_id="link-001",
                display_name="Department",
                source_property_key="dept_id",
                target_entity_id=seed_target_entity.id,
                target_property_key="dept_id",
                cardinality="1:1",
                is_optional=False,
                is_active=True,
            ).to_dict(),
        ],
        layout_state={},
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    return repo.save(revision)


@pytest.fixture
def seed_materialized_rows(db_session, seed_entity, seed_published_revision_with_computed):
    """Create materialized rows for the published revision."""
    repo = EntityMaterializationRepository(db_session)
    rows = [
        EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_id=seed_published_revision_with_computed.id,
            row_id=f"row-{i}",
            row_data={"salary": 1000 * i, "total_comp": 1100 * i},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        )
        for i in range(7)
    ]
    repo.save_rows(seed_entity.id, seed_published_revision_with_computed.id, rows)
    return rows


@pytest.fixture
def seed_deprecated_entity(db_session, tenant_context):
    """Create a deprecated entity."""
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="deprecated_entity",
        display_name="Deprecated Entity",
        description="This entity is deprecated",
        status="deprecated",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_mapping_for_deprecated(db_session, tenant_context, seed_deprecated_entity):
    """Create a mapping for the deprecated entity so it appears in search."""
    from semantic.domain import PropertyMapping, SemanticMapping
    from semantic.repository import SemanticMappingRepository

    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="deprecated-ds",
        dataset_version_id="deprecated-v1",
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


# ─── Tests ────────────────────────────────────────────────────────────────────


class TestEnhancedEntityDetail:
    def test_get_entity_returns_field_groups(
        self, client, auth_headers, seed_entity, seed_published_revision_with_computed
    ):
        """GET /api/entities/{id} returns field_groups with base and computed properties."""
        response = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "field_groups" in data
        assert len(data["field_groups"]) == 2
        assert data["field_groups"][0]["field_kind"] == "base"
        assert data["field_groups"][0]["fields"][0]["property_key"] == "salary"
        assert data["field_groups"][1]["field_kind"] == "computed"
        assert data["field_groups"][1]["fields"][0]["property_key"] == "total_comp"
        assert data["field_groups"][1]["fields"][0]["formula"] == "salary * 1.1"

    def test_get_entity_returns_materialized_preview(
        self, client, auth_headers, seed_entity, seed_published_revision_with_computed, seed_materialized_rows
    ):
        """GET /api/entities/{id} returns materialized_preview for published version."""
        response = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "materialized_preview" in data
        preview = data["materialized_preview"]
        assert len(preview) == 5
        assert preview[0]["row_data"]["salary"] == 0
        assert preview[4]["row_data"]["salary"] == 4000

    def test_get_entity_pinned_version_returns_field_groups(
        self, client, auth_headers, seed_entity, seed_published_revision_with_computed
    ):
        """GET /api/entities/{id}/versions/{n} returns pinned version with field_groups."""
        response = client.get(f"/api/entities/{seed_entity.id}/versions/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pinned_revision" in data
        assert data["pinned_revision"]["field_groups"][0]["field_kind"] == "base"
        assert data["pinned_revision"]["field_groups"][1]["field_kind"] == "computed"

    def test_get_entity_returns_link_status(
        self, client, auth_headers, seed_entity, seed_published_with_link, seed_target_entity
    ):
        """GET /api/entities/{id} includes link_status for each link."""
        response = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "link_status" in data
        assert len(data["link_status"]) == 1
        assert data["link_status"][0]["link_id"] == "link-001"
        assert data["link_status"][0]["resolvable"] is True

    def test_get_entity_returns_computed_property_warnings_for_draft(
        self, client, auth_headers, seed_entity, seed_draft_with_computed_warnings
    ):
        """GET /api/entities/{id} includes computed_property_warnings for draft."""
        response = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "draft_revision" in data
        assert data["draft_revision"]["computed_property_warnings"] is not None
        assert len(data["draft_revision"]["computed_property_warnings"]) == 1
        assert "missing_prop" in data["draft_revision"]["computed_property_warnings"][0]


class TestEntityRegistrySearch:
    def test_search_by_display_name(self, client, auth_headers, seed_entity):
        """GET /api/entities?q=... searches by display_name substring."""
        response = client.get("/api/entities?q=Detail", headers=auth_headers)
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
        response = client.get("/api/entities?q=detail_test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert any(item["object_type_key"] == seed_entity.object_type_key for item in data)

    def test_search_does_not_include_computed_property_values(
        self, client, auth_headers, seed_entity, seed_published_revision_with_computed
    ):
        """Search does not include computed property values in the index."""
        # The search query "salary * 1.1" should not match because computed property values are not indexed
        response = client.get("/api/entities?q=salary%20*%201.1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert not any(item["id"] == seed_entity.id for item in data)

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
