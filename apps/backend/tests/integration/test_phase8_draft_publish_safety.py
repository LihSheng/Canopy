"""Draft / publish safety regression tests (Issue 7, Step 2).

Draft saves accept invalid data; publish blocks it.
"""

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
        object_type_key="safety_test_entity",
        display_name="Safety Test Entity",
        description="Entity for draft/publish safety tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_target(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = repo.save(
        ObjectType(
            id=str(uuid.uuid4()),
            tenant_id=tenant_context.tenant_id,
            object_type_key="safety_target",
            display_name="Safety Target",
            description="Published target for link tests",
            created_at=datetime.now(UTC),
        )
    )
    rev_repo = EntityRevisionRepository(db_session)
    rev_repo.save(
        EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=obj.id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="t1",
                    property_key="id",
                    display_name="ID",
                    is_primary_key=True,
                ),
            ],
            source_nodes=[
                {
                    "source_id": "s1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["id"],
                }
            ],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
    )
    return obj


def _create_draft(client, auth_headers, seed_entity):
    resp = client.post(
        f"/api/entities/{seed_entity.id}/revisions",
        json={
            "properties": [
                {
                    "property_id": "p1",
                    "property_key": "name",
                    "display_name": "Name",
                    "semantic_type": "string",
                    "is_required": True,
                    "is_primary_key": True,
                    "sort_order": 1,
                },
            ],
            "source_nodes": [
                {
                    "source_id": "src-1",
                    "source_type": "dataset_table",
                    "name": "src",
                    "reference_id": "ds-001",
                    "fields": ["name"],
                }
            ],
            "source_bindings": [
                {
                    "property_key": "name",
                    "source_node_id": "src-1",
                    "source_field_name": "name",
                },
            ],
            "computed_properties": [],
            "links": [],
            "layout_state": {},
            "publish": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestDraftPublishSafety:
    def test_draft_save_with_invalid_computed_property(self, client, auth_headers, seed_entity):
        """PUT /draft accepts a computed property with syntax error."""
        _create_draft(client, auth_headers, seed_entity)
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "computed_properties": [
                    {
                        "id": "cp-bad",
                        "property_key": "bad_formula",
                        "display_name": "Bad Formula",
                        "formula": "!!!syntax_error!!!",
                        "formula_type": "arithmetic",
                        "inputs": [],
                        "output_type": "string",
                        "sort_order": 1,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(cp["property_key"] == "bad_formula" for cp in data["computed_properties"])

    def test_publish_blocks_invalid_computed_property(self, client, auth_headers, seed_entity):
        """Publish rejects draft with computed property syntax error."""
        _create_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "computed_properties": [
                    {
                        "id": "cp-bad",
                        "property_key": "bad_formula",
                        "display_name": "Bad Formula",
                        "formula": "!!!syntax_error!!!",
                        "formula_type": "arithmetic",
                        "inputs": [],
                        "output_type": "string",
                        "sort_order": 1,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        assert "syntax" in resp.json()["detail"].lower() or "publish validation failed" in resp.json()["detail"].lower()

    def test_draft_save_with_invalid_link_cardinality(self, client, auth_headers, seed_entity):
        """PUT /draft accepts a link with M:M cardinality."""
        _create_draft(client, auth_headers, seed_entity)
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-bad",
                        "display_name": "Bad Link",
                        "source_property_key": "name",
                        "target_entity_id": str(uuid.uuid4()),
                        "target_property_key": "id",
                        "cardinality": "M:M",
                        "is_optional": True,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(ln["link_id"] == "link-bad" for ln in data["links"])

    def test_publish_blocks_invalid_link_cardinality(self, client, auth_headers, seed_entity):
        """Publish rejects M:M link cardinality."""
        _create_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-bad",
                        "display_name": "Bad Link",
                        "source_property_key": "name",
                        "target_entity_id": str(uuid.uuid4()),
                        "target_property_key": "id",
                        "cardinality": "M:M",
                        "is_optional": True,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json()["detail"].lower()
        assert "cardinality" in detail or "publish validation failed" in detail

    def test_draft_save_with_broken_bindings(self, client, auth_headers, seed_entity):
        """PUT /draft accepts source bindings that reference missing properties."""
        _create_draft(client, auth_headers, seed_entity)
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_bindings": [
                    {
                        "property_key": "missing_prop",
                        "source_node_id": "src-1",
                        "source_field_name": "field",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(b["property_key"] == "missing_prop" for b in data["source_bindings"])

    def test_publish_blocks_broken_bindings(self, client, auth_headers, seed_entity):
        """Publish rejects when required property has no binding."""
        _create_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_bindings": [],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json()["detail"].lower()
        assert "binding" in detail or "publish validation failed" in detail

    def test_draft_save_with_missing_required_property_binding(self, client, auth_headers, seed_entity):
        """PUT /draft accepts a draft where a required property has no binding."""
        _create_draft(client, auth_headers, seed_entity)
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_bindings": [],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    def test_publish_blocks_missing_required_property_binding(self, client, auth_headers, seed_entity):
        """Publish fails when required property lacks source binding."""
        _create_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "source_bindings": [],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json()["detail"].lower()
        assert "binding" in detail or "publish validation failed" in detail

    def test_draft_save_with_planned_bindings_to_unpublished(self, client, auth_headers, seed_entity):
        """PUT /draft accepts planned bindings to unpublished entities."""
        _create_draft(client, auth_headers, seed_entity)
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "planned_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": str(uuid.uuid4()),
                        "source_field_name": "field",
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["planned_bindings"]) == 1

    def test_publish_blocks_planned_bindings_to_unpublished(self, client, auth_headers, seed_entity):
        """Publish rejects planned bindings referencing unpublished entities."""
        _create_draft(client, auth_headers, seed_entity)
        target_id = str(uuid.uuid4())
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "planned_bindings": [
                    {
                        "property_key": "name",
                        "source_node_id": target_id,
                        "source_field_name": "field",
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json()["detail"].lower()
        assert "planned binding" in detail or "unpublished" in detail or "publish validation failed" in detail
