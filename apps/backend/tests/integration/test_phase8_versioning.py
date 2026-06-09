"""Versioning and immutability regression tests (Issue 7, Step 3)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
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
    yield ctx


@pytest.fixture
def seed_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="version_test_entity",
        display_name="Version Test Entity",
        description="Entity for versioning tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_v1(db_session, seed_entity):
    repo = EntityRevisionRepository(db_session)
    rev = repo.save(
        EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="name",
                    display_name="Name",
                    semantic_type="string",
                    is_required=True,
                    sort_order=1,
                ),
            ],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "source_type": "table",
                    "name": "src",
                    "reference_id": "r1",
                    "fields": ["name"],
                }
            ],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
    )
    return rev


class TestVersioningAndImmutability:
    def test_published_revision_is_immutable(self, client, auth_headers, seed_entity, seed_published_v1):
        """After publish, PUT /draft returns 404 because there is no draft to mutate."""
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "properties": [
                    {
                        "property_id": "p2",
                        "property_key": "hacked",
                        "display_name": "Hacked",
                        "semantic_type": "string",
                        "sort_order": 1,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

        # Verify published revision unchanged
        resp2 = client.get(
            f"/api/entities/{seed_entity.id}/revisions/{seed_published_v1.id}",
            headers=auth_headers,
        )
        assert resp2.status_code == 200
        props = resp2.json()["properties"]
        assert len(props) == 1
        assert props[0]["property_key"] == "name"

    def test_publish_creates_new_version(self, client, auth_headers, seed_entity, seed_published_v1):
        """Fork draft then publish creates revision 2."""
        fork_resp = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert fork_resp.status_code == 201
        assert fork_resp.json()["revision_number"] == 2

        # Add source nodes so publish passes
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "table",
                        "name": "src",
                        "reference_id": "r1",
                        "fields": ["name"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": "src-1",
                        "source_field_name": "name",
                    }
                ],
            },
            headers=auth_headers,
        )

        pub_resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 200
        assert pub_resp.json()["revision_number"] == 2
        assert pub_resp.json()["status"] == "published"

    def test_only_one_published_active_and_previous_archived(
        self, client, auth_headers, db_session, seed_entity, seed_published_v1
    ):
        """After publishing v2, v1 is archived and v2 is the only published."""
        # Fork and publish v2
        client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "table",
                        "name": "src",
                        "reference_id": "r1",
                        "fields": ["name"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": "src-1",
                        "source_field_name": "name",
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        repo = EntityRevisionRepository(db_session)
        v1_after = repo.get(seed_published_v1.id)
        assert v1_after.status == RevisionStatus.ARCHIVED.value

        active = repo.get_published(seed_entity.id)
        assert active is not None
        assert active.revision_number == 2
        assert active.status == RevisionStatus.PUBLISHED.value

    def test_version_history_preserved(self, client, auth_headers, seed_entity, seed_published_v1):
        """GET /revisions lists both archived and published."""
        # Fork and publish v2
        client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "table",
                        "name": "src",
                        "reference_id": "r1",
                        "fields": ["name"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": "src-1",
                        "source_field_name": "name",
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/revisions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        statuses = {r["revision_number"]: r["status"] for r in data}
        assert statuses[1] == "archived"
        assert statuses[2] == "published"

    def test_revert_to_prior_creates_new_draft(self, client, auth_headers, seed_entity, seed_published_v1):
        """Revert to v1 creates a new draft forked from v1."""
        # Fork and publish v2 first
        client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "table",
                        "name": "src",
                        "reference_id": "r1",
                        "fields": ["name"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": "src-1",
                        "source_field_name": "name",
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        resp = client.post(
            f"/api/entities/{seed_entity.id}/revert/{seed_published_v1.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["forked_from_revision_id"] == seed_published_v1.id
        assert data["revision_number"] == 3

    def test_reverted_draft_can_be_edited_and_published(self, client, auth_headers, seed_entity, seed_published_v1):
        """After revert, edit the draft and publish again."""
        # Create v2 and publish
        client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "table",
                        "name": "src",
                        "reference_id": "r1",
                        "fields": ["name"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": "src-1",
                        "source_field_name": "name",
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        # Revert to v1
        revert_resp = client.post(
            f"/api/entities/{seed_entity.id}/revert/{seed_published_v1.id}",
            headers=auth_headers,
        )
        assert revert_resp.status_code == 201

        # Edit draft
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
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
                    {
                        "property_id": "p2",
                        "property_key": "email",
                        "display_name": "Email",
                        "semantic_type": "string",
                        "is_required": False,
                        "sort_order": 2,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-1",
                        "source_type": "table",
                        "name": "src",
                        "reference_id": "r1",
                        "fields": ["name", "email"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": "src-1",
                        "source_field_name": "name",
                    },
                    {
                        "property_key": "email",
                        "source_node_id": "src-1",
                        "source_field_name": "email",
                    },
                ],
            },
            headers=auth_headers,
        )

        # Publish
        pub_resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 200
        data = pub_resp.json()
        assert data["status"] == "published"
        assert data["revision_number"] == 3
        prop_keys = {p["property_key"] for p in data["properties"]}
        assert "email" in prop_keys
