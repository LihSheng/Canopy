"""Computed property validation and evaluation regression tests (Issue 7, Step 6)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
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
        object_type_key="computed_test_entity",
        display_name="Computed Test Entity",
        description="Entity for computed property tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


def _create_draft(client, auth_headers, seed_entity):
    resp = client.post(
        f"/api/entities/{seed_entity.id}/revisions",
        json={
            "properties": [
                {
                    "property_id": "p1",
                    "property_key": "salary",
                    "display_name": "Salary",
                    "semantic_type": "number",
                    "is_required": True,
                    "is_primary_key": True,
                    "sort_order": 1,
                },
                {
                    "property_id": "p2",
                    "property_key": "bonus",
                    "display_name": "Bonus",
                    "semantic_type": "number",
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
                    "fields": ["salary", "bonus"],
                }
            ],
            "source_bindings": [
                {
                    "property_key": "salary",
                    "source_node_id": "src-1",
                    "source_field_name": "salary",
                },
                {
                    "property_key": "bonus",
                    "source_node_id": "src-1",
                    "source_field_name": "bonus",
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


class TestComputedPropertyValidation:
    def test_valid_formula_passes_publish(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "total_comp",
                "display_name": "Total Compensation",
                "formula": "add(salary, bonus)",
                "formula_type": "arithmetic",
                "inputs": ["salary", "bonus"],
                "output_type": "number",
                "sort_order": 3,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

    def test_referencing_removed_property_fails_publish(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "bad_ref",
                "display_name": "Bad Ref",
                "formula": "multiply(missing_prop, 2)",
                "formula_type": "arithmetic",
                "inputs": ["missing_prop"],
                "output_type": "number",
                "sort_order": 3,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        pub_resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 400, pub_resp.text
        detail = pub_resp.json()["detail"].lower()
        assert "missing_prop" in detail or "publish validation failed" in detail

    def test_circular_dependency_fails_publish(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        # Add first computed property
        client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "cp_a",
                "display_name": "CP A",
                "formula": "multiply(salary, 2)",
                "formula_type": "arithmetic",
                "inputs": ["salary"],
                "output_type": "number",
                "sort_order": 3,
                "is_active": True,
            },
            headers=auth_headers,
        )
        # Add second that references first (circular-ish: cp_b -> cp_a)
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "cp_b",
                "display_name": "CP B",
                "formula": "multiply(cp_a, 2)",
                "formula_type": "arithmetic",
                "inputs": ["cp_a"],
                "output_type": "number",
                "sort_order": 4,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        pub_resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 400, pub_resp.text
        detail = pub_resp.json()["detail"].lower()
        assert "circular" in detail or "publish validation failed" in detail

    def test_syntax_error_blocks_add_endpoint(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "bad",
                "display_name": "Bad",
                "formula": "",
                "formula_type": "arithmetic",
                "inputs": [],
                "output_type": "number",
                "sort_order": 1,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_syntax_error_in_update_draft_saved_but_blocks_publish(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        resp = client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "computed_properties": [
                    {
                        "id": "cp-bad",
                        "property_key": "bad",
                        "display_name": "Bad",
                        "formula": "!!!bad!!!",
                        "formula_type": "arithmetic",
                        "inputs": [],
                        "output_type": "number",
                        "sort_order": 1,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        pub_resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert pub_resp.status_code == 400, pub_resp.text


class TestComputedPropertyEvaluation:
    def test_evaluation_in_materialized_rows(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "total_comp",
                "display_name": "Total Compensation",
                "formula": "add(salary, bonus)",
                "formula_type": "arithmetic",
                "inputs": ["salary", "bonus"],
                "output_type": "number",
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
                {"salary": 1000, "bonus": 200},
            ]
            resp = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["row_data"]["total_comp"] == 1200

    def test_evaluation_failure_produces_null(self, client, auth_headers, seed_entity):
        _create_draft(client, auth_headers, seed_entity)
        client.post(
            f"/api/entities/{seed_entity.id}/draft/computed-properties",
            json={
                "property_key": "bad_div",
                "display_name": "Bad Division",
                "formula": "divide(salary, bonus)",
                "formula_type": "arithmetic",
                "inputs": ["salary", "bonus"],
                "output_type": "number",
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
                {"salary": 1000, "bonus": None},
            ]
            resp = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp.status_code == 200, resp.text

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["row_data"]["bad_div"] is None

    def test_evaluate_endpoint_dry_run(self, client, auth_headers, seed_entity):
        resp = client.post(
            f"/api/entities/{seed_entity.id}/computed-properties/evaluate",
            json={
                "formula": 'concat("Hello", " ", "World")',
                "inputs": [],
                "sample_row": {},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["result"] == "Hello World"
        assert data["errors"] == []
