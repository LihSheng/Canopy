"""Integration tests for entity version pinning API."""

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


@pytest.fixture(autouse=True)
def tenant_context():
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    return ctx


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
    """Create an entity for version pinning tests."""
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="version_pin_test_entity",
        display_name="Version Pin Test Entity",
        description="Entity for version pinning integration tests",
        status="published",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_revision(db_session, seed_entity):
    """Create a published revision (v1)."""
    now = datetime.now(UTC)
    repo = EntityRevisionRepository(db_session)
    rev = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=1,
        status=RevisionStatus.PUBLISHED.value,
        properties=[
            EntityProperty(
                property_id="p1", property_key="name", display_name="Name", semantic_type="string", sort_order=1
            ),
        ],
        source_bindings=[],
        links=[],
        source_nodes=[],
        computed_properties=[],
        layout_state={},
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    return repo.save(rev)


@pytest.fixture
def seed_second_published_revision(db_session, seed_entity, seed_published_revision):
    """Create a second published revision (v2) and archive v1."""
    now = datetime.now(UTC)
    repo = EntityRevisionRepository(db_session)

    # Archive v1
    v1 = repo.get(seed_published_revision.id)
    v1.status = RevisionStatus.ARCHIVED.value
    v1.updated_at = now
    repo.save(v1)

    # Create v2 as published
    rev = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=2,
        status=RevisionStatus.PUBLISHED.value,
        properties=[
            EntityProperty(
                property_id="p1", property_key="name", display_name="Name v2", semantic_type="string", sort_order=1
            ),
            EntityProperty(
                property_id="p2", property_key="email", display_name="Email", semantic_type="string", sort_order=2
            ),
        ],
        source_bindings=[],
        links=[],
        source_nodes=[],
        computed_properties=[],
        layout_state={},
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    return repo.save(rev)


class TestVersionPinning:
    def test_get_latest_published_entity(self, client, auth_headers, seed_entity, seed_published_revision):
        """GET /entities/{id}/versions/latest returns the latest published revision detail."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/latest",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == seed_entity.id
        assert data["published_revision"] is not None
        assert data["published_revision"]["revision_number"] == 1
        assert data["published_revision"]["status"] == "published"

    def test_get_latest_returns_active_published_only(
        self, client, auth_headers, seed_entity, seed_second_published_revision
    ):
        """When there are archived versions, latest returns only the active published."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/latest",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["published_revision"]["revision_number"] == 2
        assert data["published_revision"]["status"] == "published"

    def test_get_specific_version_by_revision_number(self, client, auth_headers, seed_entity, seed_published_revision):
        """GET /entities/{id}/versions/{revision_number} returns entity at that version."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/1",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == seed_entity.id
        assert data["pinned_revision"] is not None
        assert data["pinned_revision"]["revision_number"] == 1
        assert data["pinned_revision"]["status"] == "published"

    def test_get_specific_version_not_found(self, client, auth_headers, seed_entity):
        """GET /entities/{id}/versions/{n} returns 404 for nonexistent version."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_pin_to_draft_version_rejected(
        self, client, auth_headers, db_session, seed_entity, seed_published_revision
    ):
        """Version pinning to a draft revision returns 404 (only published versions exposed)."""
        now = datetime.now(UTC)
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=5,
            status=RevisionStatus.DRAFT.value,
            properties=seed_published_revision.properties,
            source_bindings=[],
            links=[],
            source_nodes=[],
            computed_properties=[],
            layout_state={},
            created_at=now,
            updated_at=now,
        )
        repo.save(draft)

        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/5",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_latest_published_returns_404_when_no_published(self, client, auth_headers, seed_entity):
        """GET /entities/{id}/versions/latest returns 404 when no published revision exists."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/latest",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_specific_archived_version(
        self, client, auth_headers, seed_entity, seed_second_published_revision, seed_published_revision
    ):
        """GET /entities/{id}/versions/{n} can fetch an archived (previously published) version."""
        # seed_published_revision is now archived (v1), seed_second_published_revision is active (v2)
        response = client.get(
            f"/api/entities/{seed_entity.id}/versions/1",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["pinned_revision"]["revision_number"] == 1
        assert data["pinned_revision"]["status"] == "archived"


class TestPublishFlowRegression:
    """Regression tests verifying the publish → immutable → single-active contract."""

    def test_publish_creates_immutable_version(self, client, auth_headers, db_session, tenant_context):
        """Publishing a draft creates a new published revision that cannot be mutated."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="regression_pub_test",
                display_name="Regression Publish Test",
                description="Testing publish immutability",
                created_at=datetime.now(UTC),
            )
        )

        # Create initial revision and publish via API
        resp = client.post(
            f"/api/entities/{entity_id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": "p1",
                        "property_key": "name",
                        "display_name": "Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "sort_order": 1,
                    },
                ],
                "source_nodes": [
                    {"source_id": "s1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                "publish": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        published_data = resp.json()
        assert published_data["status"] == "published"
        revision_id = published_data["id"]

        # Try to update the published revision directly (via update_draft) — should fail
        resp2 = client.put(
            f"/api/entities/{entity_id}/draft",
            json={
                "properties": [
                    {
                        "property_id": "p2",
                        "property_key": "hacked",
                        "display_name": "Hacked",
                        "semantic_type": "string",
                        "sort_order": 1,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert resp2.status_code == 404  # No draft exists after publish

        # Verify the published revision is unchanged
        resp3 = client.get(
            f"/api/entities/{entity_id}/revisions/{revision_id}",
            headers=auth_headers,
        )
        assert resp3.status_code == 200
        props = resp3.json()["properties"]
        assert len(props) == 1
        assert props[0]["property_key"] == "name"

    def test_only_one_published_version_active(self, client, auth_headers, db_session, tenant_context):
        """Publishing a second draft archives the previous published revision.
        Only one published revision is active at a time."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="single_active_test",
                display_name="Single Active Publish Test",
                description="Only one published at a time",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)

        # Create and publish v1
        v1 = rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[EntityProperty(property_id="p1", property_key="v1_prop", display_name="V1 Prop")],
                source_bindings=[],
                links=[],
                source_nodes=[],
                computed_properties=[],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )

        active = rev_repo.get_published(entity_id)
        assert active is not None
        assert active.revision_number == 1

        # Create and publish v2 via API (fork draft then publish)
        fork_resp = client.post(
            f"/api/entities/{entity_id}/draft",
            headers=auth_headers,
        )
        assert fork_resp.status_code == 201

        # Set source nodes on draft for publish validation
        client.put(
            f"/api/entities/{entity_id}/draft",
            json={
                "source_nodes": [
                    {"source_id": "s1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
            },
            headers=auth_headers,
        )

        pub_resp = client.post(
            f"/api/entities/{entity_id}/draft/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 200

        # Now v1 should be archived
        v1_after = rev_repo.get(v1.id)
        assert v1_after.status == RevisionStatus.ARCHIVED.value

        # Only one active published
        active2 = rev_repo.get_published(entity_id)
        assert active2 is not None
        assert active2.revision_number == 2
        assert active2.status == RevisionStatus.PUBLISHED.value

        # Verify only one published via the status endpoint
        status_resp = client.get(
            f"/api/entities/{entity_id}/status",
            headers=auth_headers,
        )
        assert status_resp.json()["has_published"] is True
        assert status_resp.json()["published_revision_number"] == 2

    def test_draft_save_without_publish(self, client, auth_headers, db_session, tenant_context):
        """Draft can be saved/updated without publishing."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="draft_only_test",
                display_name="Draft Only Test",
                description="Testing draft save without publish",
                created_at=datetime.now(UTC),
            )
        )

        # Create a published revision first (required for fork)
        rev_repo = EntityRevisionRepository(db_session)
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[EntityProperty(property_id="p1", property_key="base", display_name="Base")],
                source_bindings=[],
                links=[],
                source_nodes=[],
                computed_properties=[],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )

        # Fork a draft
        fork_resp = client.post(
            f"/api/entities/{entity_id}/draft",
            headers=auth_headers,
        )
        assert fork_resp.status_code == 201
        draft_data = fork_resp.json()
        assert draft_data["status"] == "draft"
        draft_id = draft_data["id"]

        # Update the draft without publishing
        update_resp = client.put(
            f"/api/entities/{entity_id}/draft",
            json={
                "properties": [
                    {
                        "property_id": "p2",
                        "property_key": "extra",
                        "display_name": "Extra Field",
                        "semantic_type": "string",
                        "sort_order": 2,
                    },
                ],
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "draft"

        # Verify draft is still a draft (not published)
        get_resp = client.get(
            f"/api/entities/{entity_id}/draft",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "draft"
        assert get_resp.json()["id"] == draft_id

        # Entity should still have original published
        published = rev_repo.get_published(entity_id)
        assert published is not None
        assert published.revision_number == 1
