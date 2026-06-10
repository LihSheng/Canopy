"""End-to-end test for full entity lifecycle (Issue 7, Step 1).

Covers: create entity -> draft -> add properties/bindings/computed/link ->
publish -> materialize -> read -> link resolution.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import (
    EntityProperty,
    EntityRevision,
    LinkCardinality,
    RevisionStatus,
)
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
        object_type_key="lifecycle_entity",
        display_name="Lifecycle Entity",
        description="Full lifecycle test entity",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


def _create_initial_draft(client, auth_headers, seed_entity):
    resp = client.post(
        f"/api/entities/{seed_entity.id}/revisions",
        json={
            "properties": [
                {
                    "property_id": "p1",
                    "property_key": "first_name",
                    "display_name": "First Name",
                    "semantic_type": "string",
                    "is_required": True,
                    "is_primary_key": True,
                    "sort_order": 1,
                },
                {
                    "property_id": "p2",
                    "property_key": "last_name",
                    "display_name": "Last Name",
                    "semantic_type": "string",
                    "is_required": True,
                    "sort_order": 2,
                },
            ],
            "source_nodes": [
                {
                    "source_id": "src-1",
                    "source_type": "dataset_table",
                    "name": "employees",
                    "reference_id": "ds-001",
                    "fields": ["first_name", "last_name"],
                }
            ],
            "computed_properties": [],
            "links": [],
            "layout_state": {},
            "publish": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text

    # Set bindings separately to avoid a schema bug in create_initial_revision
    bind_resp = client.put(
        f"/api/entities/{seed_entity.id}/draft/bindings",
        json={
            "bindings": [
                {
                    "property_key": "first_name",
                    "source_node_id": "src-1",
                    "source_field_name": "first_name",
                },
                {
                    "property_key": "last_name",
                    "source_node_id": "src-1",
                    "source_field_name": "last_name",
                },
            ]
        },
        headers=auth_headers,
    )
    assert bind_resp.status_code == 200, bind_resp.text
    return resp.json()


class TestFullEntityLifecycle:
    def test_01_create_entity_and_draft(self, client, auth_headers, seed_entity):
        data = _create_initial_draft(client, auth_headers, seed_entity)
        assert data["status"] == "draft"
        assert data["revision_number"] == 1
        assert len(data["properties"]) == 2

    def test_02_add_computed_property(self, client, auth_headers, seed_entity):
        _create_initial_draft(client, auth_headers, seed_entity)
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "full_name",
                "display_name": "Full Name",
                "formula": 'concat(first_name, " ", last_name)',
                "formula_type": "arithmetic",
                "output_type": "string",
                "sort_order": 3,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert any(cp["property_key"] == "full_name" for cp in data["computed_properties"])

    def test_03_publish_entity(self, client, auth_headers, seed_entity):
        _create_initial_draft(client, auth_headers, seed_entity)
        client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "full_name",
                "display_name": "Full Name",
                "formula": 'concat(first_name, " ", last_name)',
                "formula_type": "arithmetic",
                "output_type": "string",
                "sort_order": 3,
                "is_active": True,
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "published"
        assert any(cp["property_key"] == "full_name" for cp in data["computed_properties"])

    def test_04_materialize_and_verify_computed(self, client, auth_headers, seed_entity):
        _create_initial_draft(client, auth_headers, seed_entity)
        client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "full_name",
                "display_name": "Full Name",
                "formula": 'concat(first_name, " ", last_name)',
                "formula_type": "arithmetic",
                "output_type": "string",
                "sort_order": 3,
                "is_active": True,
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"first_name": "Alice", "last_name": "Chen"},
                {"first_name": "Bob", "last_name": "Martinez"},
            ]
            resp = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        stats = resp.json()
        assert stats["rows_inserted"] == 2

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) == 2
        names = {r["row_data"]["full_name"] for r in rows}
        assert "Alice Chen" in names
        assert "Bob Martinez" in names

    def test_05_link_resolution(self, client, auth_headers, db_session, tenant_context, seed_entity):
        # Create and publish target entity (Department)
        target_repo = ObjectTypeRepository(db_session)
        dept = target_repo.save(
            ObjectType(
                id=str(uuid.uuid4()),
                tenant_id=tenant_context.tenant_id,
                object_type_key="lifecycle_dept",
                display_name="Lifecycle Department",
                description="Target department",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        dept_rev = rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=dept.id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[
                    EntityProperty(
                        property_id="d1",
                        property_key="dept_id",
                        display_name="Dept ID",
                        is_primary_key=True,
                    ),
                ],
                source_nodes=[
                    {
                        "source_id": "s-dept",
                        "source_type": "table",
                        "name": "depts",
                        "reference_id": "r1",
                        "fields": ["dept_id"],
                    }
                ],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )
        mat_repo = EntityMaterializationRepository(db_session)
        mat_repo.save_rows(
            dept.id,
            dept_rev.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=dept.id,
                    revision_id=dept_rev.id,
                    row_id="dept-1",
                    row_data={"dept_id": "dept-1"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        # Setup source entity with link via draft update
        _create_initial_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "properties": [
                    {
                        "property_id": "p1",
                        "property_key": "first_name",
                        "display_name": "First Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    },
                    {
                        "property_id": "p2",
                        "property_key": "last_name",
                        "display_name": "Last Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "sort_order": 2,
                    },
                    {
                        "property_id": "p3",
                        "property_key": "dept_ref",
                        "display_name": "Dept Ref",
                        "semantic_type": "string",
                        "is_required": False,
                        "sort_order": 3,
                    },
                ],
                "links": [
                    {
                        "link_id": "link-dept",
                        "display_name": "Department",
                        "source_property_key": "dept_ref",
                        "target_entity_id": dept.id,
                        "target_property_key": "dept_id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        client.put(
            f"/api/entities/{seed_entity.id}/draft/bindings",
            json={
                "bindings": [
                    {
                        "property_key": "first_name",
                        "source_node_id": "src-1",
                        "source_field_name": "first_name",
                    },
                    {
                        "property_key": "last_name",
                        "source_node_id": "src-1",
                        "source_field_name": "last_name",
                    },
                    {
                        "property_key": "dept_ref",
                        "source_node_id": "src-1",
                        "source_field_name": "dept_ref",
                    },
                ]
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        # Materialize source rows
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {
                    "first_name": "Alice",
                    "last_name": "Chen",
                    "dept_ref": "dept-1",
                },
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/links/link-dept/resolve",
            params={"row_id": "Alice"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["row_id"] == "dept-1"
