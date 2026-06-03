"""Integration tests for Entity Revision API (draft, publish, revision lifecycle)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus
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
    """Create a bare object type (entity) for revision tests."""
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="revision_test_employee",
        display_name="Revision Test Employee",
        description="Entity for revision lifecycle tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_revision(db_session, tenant_context, seed_entity):
    """Create a published revision with properties for fork tests."""
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
                property_key="employee_id",
                display_name="Employee ID",
                semantic_type="integer",
                is_required=True,
                is_primary_key=True,
                sort_order=1,
            ),
            EntityProperty(
                property_id="prop-002",
                property_key="employee_name",
                display_name="Employee Name",
                semantic_type="string",
                is_required=True,
                sort_order=2,
            ),
            EntityProperty(
                property_id="prop-003",
                property_key="department",
                display_name="Department",
                semantic_type="string",
                is_required=False,
                sort_order=3,
            ),
        ],
        links=[],
        source_nodes=[
            {
                "source_id": "src-1",
                "source_type": "dataset_table",
                "name": "employees_csv",
                "reference_id": "ds-ref-1",
                "fields": ["id", "name", "dept"],
            }
        ],
        computed_properties=[],
        layout_state={},
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    return repo.save(revision)


# ─── Tests ────────────────────────────────────────────────────────────────────


class TestEntityRevisionLifecycle:
    """Test the full draft → publish lifecycle."""

    def test_create_initial_revision_as_draft(self, client, auth_headers, seed_entity):
        """POST /api/entities/{id}/revisions creates initial revision as draft."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": "prop-001",
                        "property_key": "id",
                        "display_name": "ID",
                        "semantic_type": "integer",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    }
                ],
                "links": [],
                "source_nodes": [],
                "computed_properties": [],
                "layout_state": {},
                "publish": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["status"] == "draft"
        assert data["revision_number"] == 1
        assert len(data["properties"]) == 1
        assert data["properties"][0]["property_id"] == "prop-001"

    def test_create_initial_revision_published(self, client, auth_headers, seed_entity):
        """POST /api/entities/{id}/revisions with publish=True creates published revision."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": "prop-001",
                        "property_key": "id",
                        "display_name": "ID",
                        "semantic_type": "integer",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    }
                ],
                "links": [],
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "dataset_table",
                        "name": "employees",
                        "reference_id": "ds-ref",
                        "fields": ["id", "name"],
                    }
                ],
                "publish": True,
                "source_dependencies": [
                    {"dependency_type": "dataset", "dependency_id": "ds-001"},
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None

    def test_entity_status_shows_nothing_for_new_entity(self, client, auth_headers, seed_entity):
        """GET /api/entities/{id}/status returns empty state for entity with no revisions."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_published"] is False
        assert data["has_draft"] is False

    def test_entity_status_shows_published(self, client, auth_headers, seed_published_revision, seed_entity):
        """GET /api/entities/{id}/status shows published revision info."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_published"] is True
        assert data["has_draft"] is False
        assert data["published_revision_number"] == 1


class TestForkDraft:
    """Test forking a draft from a published revision."""

    def test_fork_draft_from_published(self, client, auth_headers, seed_published_revision, seed_entity):
        """POST /api/entities/{id}/draft creates a new draft forked from published."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["status"] == "draft"
        assert data["revision_number"] == 2
        assert data["forked_from_revision_id"] == seed_published_revision.id
        assert data["lock_holder_id"] is not None  # Locked to auth user
        assert len(data["properties"]) == 3  # Copied from published

    def test_fork_draft_copies_properties(self, client, auth_headers, seed_published_revision, seed_entity):
        """Draft forked from published has identical properties."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        prop_keys = {p["property_key"] for p in data["properties"]}
        assert "employee_id" in prop_keys
        assert "employee_name" in prop_keys
        assert "department" in prop_keys

    def test_fork_draft_fails_when_draft_exists(self, client, auth_headers, seed_published_revision, seed_entity):
        """Cannot fork a second draft when one already exists."""
        # Create first draft
        r1 = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert r1.status_code == 201

        # Try to create second draft
        r2 = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert r2.status_code == 400
        assert "active draft" in r2.json()["detail"].lower()

    def test_fork_draft_requires_existing_revision(self, client, auth_headers, seed_entity):
        """Forking requires at least one existing revision (published or otherwise)."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "no published revision" in response.json()["detail"].lower()


class TestUpdateDraft:
    """Test updating draft content."""

    @pytest.fixture
    def seed_draft(self, db_session, seed_published_revision, seed_entity):
        """Create an active draft revision for update tests."""
        now = datetime.now(UTC)
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=seed_published_revision.id,
            properties=seed_published_revision.properties,
            links=seed_published_revision.links,
            source_nodes=seed_published_revision.source_nodes,
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user-1",
            locked_at=now,
            created_at=now,
            updated_at=now,
        )
        return repo.save(draft)

    def test_update_draft_properties(self, client, auth_headers, seed_entity, seed_draft):
        """PUT /api/entities/{id}/draft updates draft properties."""
        response = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "properties": [
                    {
                        "property_id": "prop-001",
                        "property_key": "employee_id",
                        "display_name": "Staff ID",
                        "semantic_type": "integer",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    },
                    {
                        "property_id": "prop-004",
                        "property_key": "updated_at",
                        "display_name": "Last Updated",
                        "semantic_type": "datetime",
                        "is_required": False,
                        "sort_order": 4,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data["properties"]) == 2
        assert data["properties"][0]["display_name"] == "Staff ID"
        # Verify entity still has one active draft
        status_resp = client.get(
            f"/api/entities/{seed_entity.id}/status",
            headers=auth_headers,
        )
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status["has_draft"] is True
        assert status["has_published"] is True


class TestDiscardDraft:
    """Test discarding a draft."""

    @pytest.fixture
    def seed_draft(self, db_session, seed_published_revision, seed_entity):
        now = datetime.now(UTC)
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=seed_published_revision.id,
            properties=seed_published_revision.properties,
            links=[],
            source_nodes=[],
            computed_properties=[],
            layout_state={},
            lock_holder_id=None,
            locked_at=None,
            created_at=now,
            updated_at=now,
        )
        return repo.save(draft)

    def test_discard_draft(self, client, auth_headers, seed_entity, seed_draft):
        """DELETE /api/entities/{id}/draft discards the active draft."""
        response = client.delete(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["discarded"] is True

        # Verify no draft exists anymore
        get_resp = client.get(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        assert get_resp.json() is None

    def test_discard_draft_none_exists(self, client, auth_headers, seed_entity):
        """Discarding when no draft exists returns 404."""
        response = client.delete(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_discard_draft_rejected_when_locked_by_another(
        self, client, auth_headers, db_session, seed_published_revision, seed_entity
    ):
        """Cannot discard a draft locked by another user."""
        now = datetime.now(UTC)
        repo = EntityRevisionRepository(db_session)
        locked_draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=seed_published_revision.id,
            properties=seed_published_revision.properties,
            links=[],
            source_nodes=[],
            computed_properties=[],
            layout_state={},
            lock_holder_id="other-user",
            locked_at=now,
            created_at=now,
            updated_at=now,
        )
        repo.save(locked_draft)

        response = client.delete(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "locked by another user" in response.json()["detail"].lower()


class TestPublishDraft:
    """Test publishing a draft."""

    @pytest.fixture
    def seed_draft_with_binding(self, db_session, seed_published_revision, seed_entity):
        """Create a draft with a source_node binding for publish validation."""
        now = datetime.now(UTC)
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=seed_published_revision.id,
            properties=seed_published_revision.properties,
            links=[],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "source_type": "dataset_table",
                    "name": "employees_csv",
                    "reference_id": "ds-ref-1",
                    "fields": ["employee_id", "employee_name", "department"],
                }
            ],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user-1",
            locked_at=now,
            created_at=now,
            updated_at=now,
        )
        return repo.save(draft)

    def test_publish_draft(self, client, auth_headers, seed_entity, seed_draft_with_binding):
        """POST /api/entities/{id}/draft/publish publishes the draft."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            json={
                "source_dependencies": [
                    {"dependency_type": "dataset", "dependency_id": "ds-001"},
                ]
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None
        assert data["lock_holder_id"] is None  # Lock released on publish

        # Verify via status endpoint
        status_resp = client.get(
            f"/api/entities/{seed_entity.id}/status",
            headers=auth_headers,
        )
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status["has_published"] is True
        assert status["published_revision_number"] == 2  # New published

    @pytest.fixture
    def seed_draft(self, db_session, seed_published_revision, seed_entity):
        """Create a draft with no source_nodes for publish-validation test."""
        now = datetime.now(UTC)
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=seed_published_revision.id,
            properties=seed_published_revision.properties,
            links=[],
            source_nodes=[],  # No source nodes — will fail publish validation
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user-1",
            locked_at=now,
            created_at=now,
            updated_at=now,
        )
        return repo.save(draft)

    def test_publish_draft_without_binding_fails(self, client, auth_headers, seed_entity, seed_draft):
        """Publishing draft with no source_nodes fails validation."""

        response = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            json={
                "source_dependencies": [
                    {"dependency_type": "dataset", "dependency_id": "ds-001"},
                ]
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "source node" in response.json()["detail"].lower()


class TestListRevisions:
    """Test listing revisions for an entity."""

    def test_list_revisions(self, client, auth_headers, seed_published_revision, seed_entity):
        """GET /api/entities/{id}/revisions lists all revisions."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/revisions",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) >= 1
        assert data[0]["status"] == "published"
        assert data[0]["revision_number"] == 1

    def test_list_revisions_empty_for_new_entity(self, client, auth_headers, seed_entity):
        """New entity with no revisions returns empty list."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/revisions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestEntityRegistryWithRevisions:
    """Test that entity registry API returns revision status."""

    def test_registry_shows_status(self, client, auth_headers, seed_published_revision, seed_entity):
        """GET /api/entities includes has_published_revision and has_draft."""
        response = client.get("/api/entities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        items = [r for r in data if r["id"] == seed_entity.id]
        assert len(items) == 1
        item = items[0]
        assert item["has_published_revision"] is True
        assert item["has_draft"] is False
        assert item["published_revision_number"] == 1

    def test_entity_detail_shows_status(self, client, auth_headers, seed_published_revision, seed_entity):
        """GET /api/entities/{id} includes revision state fields."""
        response = client.get(
            f"/api/entities/{seed_entity.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_published_revision"] is True
        assert data["has_draft"] is False
        assert data["published_revision_number"] == 1
        assert data["draft_lock_holder_id"] is None
        assert data["draft_revision_number"] is None
