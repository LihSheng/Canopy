"""Comprehensive end-to-end regression scenario (Issue 7, Step 9).

Runs the full Phase 8 lifecycle across two entities:
Department -> Employee with computed property and link.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import (
    LinkCardinality,
)
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


class TestFullRegressionScenario:
    def test_comprehensive_e2e(self, client, auth_headers, db_session, tenant_context):
        # ── 1. Create Department entity ─────────────────────────────────────────
        object_repo = ObjectTypeRepository(db_session)
        dept = object_repo.save(
            ObjectType(
                id=str(uuid.uuid4()),
                tenant_id=tenant_context.tenant_id,
                object_type_key="regression_department",
                display_name="Regression Department",
                description="Department entity for regression",
                created_at=datetime.now(UTC),
            )
        )

        # ── 2. Publish Department ───────────────────────────────────────────────
        resp = client.post(
            f"/api/entities/{dept.id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": "d1",
                        "property_key": "dept_id",
                        "display_name": "Department ID",
                        "semantic_type": "string",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    },
                    {
                        "property_id": "d2",
                        "property_key": "dept_name",
                        "display_name": "Department Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "sort_order": 2,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-dept",
                        "source_type": "dataset_table",
                        "name": "departments",
                        "reference_id": "ds-dept",
                        "fields": ["dept_id", "dept_name"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "dept_id",
                        "source_node_id": "src-dept",
                        "source_field_name": "dept_id",
                    },
                    {
                        "property_key": "dept_name",
                        "source_node_id": "src-dept",
                        "source_field_name": "dept_name",
                    },
                ],
                "publish": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        dept_rev = resp.json()
        assert dept_rev["status"] == "published"

        # ── 3. Create Employee entity with computed property + link ────────────
        emp = object_repo.save(
            ObjectType(
                id=str(uuid.uuid4()),
                tenant_id=tenant_context.tenant_id,
                object_type_key="regression_employee",
                display_name="Regression Employee",
                description="Employee entity for regression",
                created_at=datetime.now(UTC),
            )
        )

        resp = client.post(
            f"/api/entities/{emp.id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": "e1",
                        "property_key": "first_name",
                        "display_name": "First Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    },
                    {
                        "property_id": "e2",
                        "property_key": "last_name",
                        "display_name": "Last Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "sort_order": 2,
                    },
                    {
                        "property_id": "e3",
                        "property_key": "dept_ref",
                        "display_name": "Department Ref",
                        "semantic_type": "string",
                        "is_required": False,
                        "sort_order": 3,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-emp",
                        "source_type": "dataset_table",
                        "name": "employees",
                        "reference_id": "ds-emp",
                        "fields": ["first_name", "last_name", "dept_ref"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "first_name",
                        "source_node_id": "src-emp",
                        "source_field_name": "first_name",
                    },
                    {
                        "property_key": "last_name",
                        "source_node_id": "src-emp",
                        "source_field_name": "last_name",
                    },
                    {
                        "property_key": "dept_ref",
                        "source_node_id": "src-emp",
                        "source_field_name": "dept_ref",
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

        # Add computed property
        resp = client.post(
            f"/api/entities/{emp.id}/draft/computed-properties",
            json={
                "property_key": "full_name",
                "display_name": "Full Name",
                "formula": 'concat(first_name, " ", last_name)',
                "formula_type": "arithmetic",
                "inputs": ["first_name", "last_name"],
                "output_type": "string",
                "sort_order": 4,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

        # Add link to Department
        resp = client.put(
            f"/api/entities/{emp.id}/draft",
            json={
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
        assert resp.status_code == 200, resp.text

        # ── 4. Publish Employee ────────────────────────────────────────────────
        resp = client.post(
            f"/api/entities/{emp.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        emp_v1 = resp.json()
        assert emp_v1["status"] == "published"
        assert emp_v1["revision_number"] == 1

        # ── 5. Materialize both entities ──────────────────────────────────────
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"dept_id": "dept-1", "dept_name": "Engineering"},
            ]
            resp = client.post(
                f"/api/entities/{dept.id}/materialize",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text

        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {
                    "first_name": "Alice",
                    "last_name": "Chen",
                    "dept_ref": "dept-1",
                },
                {
                    "first_name": "Bob",
                    "last_name": "Martinez",
                    "dept_ref": "dept-1",
                },
            ]
            resp = client.post(
                f"/api/entities/{emp.id}/materialize",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["rows_inserted"] == 2

        # ── 6. Read Employee rows and verify computed property ─────────────────
        resp = client.get(
            f"/api/entities/{emp.id}/materialized",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        emp_rows = resp.json()
        assert len(emp_rows) == 2
        names = {r["row_data"]["full_name"] for r in emp_rows}
        assert "Alice Chen" in names
        assert "Bob Martinez" in names

        # ── 7. Resolve Department link from Employee row ──────────────────────
        resp = client.get(
            f"/api/entities/{emp.id}/links/link-dept/resolve",
            params={"row_id": "Alice"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        target_row = resp.json()
        assert target_row["row_id"] == "dept-1"
        assert target_row["row_data"]["dept_name"] == "Engineering"

        # ── 8. Pin to v1 and verify ────────────────────────────────────────────
        resp = client.get(
            f"/api/entities/{emp.id}/materialized?version=1",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        pinned_rows = resp.json()
        assert len(pinned_rows) == 2
        assert pinned_rows[0]["row_data"]["full_name"] == "Alice Chen"

        # ── 9. Create new draft, add property, publish ─────────────────────────
        resp = client.post(
            f"/api/entities/{emp.id}/draft",
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

        # Update draft with new property + binding
        resp = client.put(
            f"/api/entities/{emp.id}/draft",
            json={
                "properties": [
                    {
                        "property_id": "e1",
                        "property_key": "first_name",
                        "display_name": "First Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "is_primary_key": True,
                        "sort_order": 1,
                    },
                    {
                        "property_id": "e2",
                        "property_key": "last_name",
                        "display_name": "Last Name",
                        "semantic_type": "string",
                        "is_required": True,
                        "sort_order": 2,
                    },
                    {
                        "property_id": "e3",
                        "property_key": "dept_ref",
                        "display_name": "Department Ref",
                        "semantic_type": "string",
                        "is_required": False,
                        "sort_order": 3,
                    },
                    {
                        "property_id": "e4",
                        "property_key": "email",
                        "display_name": "Email",
                        "semantic_type": "string",
                        "is_required": False,
                        "sort_order": 4,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-emp",
                        "source_type": "dataset_table",
                        "name": "employees",
                        "reference_id": "ds-emp",
                        "fields": ["first_name", "last_name", "dept_ref", "email"],
                    }
                ],
                "source_bindings": [
                    {
                        "property_key": "first_name",
                        "source_node_id": "src-emp",
                        "source_field_name": "first_name",
                    },
                    {
                        "property_key": "last_name",
                        "source_node_id": "src-emp",
                        "source_field_name": "last_name",
                    },
                    {
                        "property_key": "dept_ref",
                        "source_node_id": "src-emp",
                        "source_field_name": "dept_ref",
                    },
                    {
                        "property_key": "email",
                        "source_node_id": "src-emp",
                        "source_field_name": "email",
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
        assert resp.status_code == 200, resp.text

        resp = client.post(
            f"/api/entities/{emp.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        emp_v2 = resp.json()
        assert emp_v2["status"] == "published"
        assert emp_v2["revision_number"] == 2

        # ── 10. Verify old version archived, new active ────────────────────────
        resp = client.get(
            f"/api/entities/{emp.id}/revisions",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        revisions = resp.json()
        statuses = {r["revision_number"]: r["status"] for r in revisions}
        assert statuses[1] == "archived"
        assert statuses[2] == "published"

        # ── 11. Verify tombstones for deleted rows ────────────────────────────
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {
                    "first_name": "Alice",
                    "last_name": "Chen",
                    "dept_ref": "dept-1",
                    "email": "alice@example.com",
                },
            ]
            resp = client.post(
                f"/api/entities/{emp.id}/materialize",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["rows_tombstoned"] == 1

        # Normal read excludes tombstone
        resp = client.get(
            f"/api/entities/{emp.id}/materialized",
            headers=auth_headers,
        )
        assert len(resp.json()) == 1

        # Audit read includes tombstone
        resp = client.get(
            f"/api/entities/{emp.id}/materialized?include_tombstones=true",
            headers=auth_headers,
        )
        rows = resp.json()
        assert len(rows) == 2
        tombstoned = [r for r in rows if r["is_tombstone"]]
        assert len(tombstoned) == 1
        assert tombstoned[0]["row_data"]["first_name"] == "Bob"

        # ── 12. Deprecate Employee ─────────────────────────────────────────────
        resp = client.post(
            f"/api/entities/{emp.id}/deprecate",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        dep_data = resp.json()
        assert dep_data["deprecated"] is True
        assert dep_data["status"] == "deprecated"

        # ── 13. Verify hidden from normal listing, visible in historical view ──
        resp = client.get("/api/entities", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        normal_ids = {r["id"] for r in resp.json()}
        assert emp.id not in normal_ids

        resp = client.get("/api/entities?include_deprecated=true", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        historical_ids = {r["id"] for r in resp.json()}
        assert emp.id in historical_ids
