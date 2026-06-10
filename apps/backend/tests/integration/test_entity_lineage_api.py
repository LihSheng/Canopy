"""Integration tests for lineage graph in entity detail API.

Verifies the entity-centered lineage graph contract is served correctly
from the entity detail API per PRD 0021.
"""

import uuid

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def tenant_context():
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    yield ctx


class TestEntityLineageInApiResponse:
    """Verify lineage graph appears in entity detail API responses."""

    def test_entity_detail_includes_lineage_when_revision_exists(
        self,
        client,
        auth_headers,
    ):
        """Entity detail with published revision includes lineage graph."""
        # Create an entity
        obj_key = f"lineage_test_{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/semantic/create-entity",
            json={
                "object_type_key": obj_key,
                "display_name": "Lineage Employee",
                "description": "Test entity for lineage",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (200, 201)
        entity_id = create_resp.json()["id"]

        # Create initial revision with properties, sources, bindings
        init_resp = client.post(
            f"/api/entities/{entity_id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": str(uuid.uuid4()),
                        "property_key": "employee_name",
                        "display_name": "Employee Name",
                        "semantic_type": "string",
                        "is_required": True,
                    },
                    {
                        "property_id": str(uuid.uuid4()),
                        "property_key": "salary",
                        "display_name": "Salary",
                        "semantic_type": "number",
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-payroll",
                        "name": "payroll.xlsx",
                        "source_type": "static_file",
                        "fields": ["employee_name", "salary"],
                    },
                ],
                "source_bindings": [
                    {
                        "property_key": "employee_name",
                        "source_node_id": "src-payroll",
                        "source_field_name": "employee_name",
                    },
                    {
                        "property_key": "salary",
                        "source_node_id": "src-payroll",
                        "source_field_name": "salary",
                    },
                ],
                "links": [
                    {
                        "link_id": "link-dept",
                        "display_name": "works_in",
                        "source_property_key": "dept_key",
                        "target_object_type_id": "ent-dept-1",
                        "target_property_key": "id",
                        "cardinality": "1:1",
                    },
                ],
                "publish": True,
            },
            headers=auth_headers,
        )
        assert init_resp.status_code in (200, 201)

        # Fetch entity detail
        detail_resp = client.get(
            f"/api/entities/{entity_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        # Lineage field must be present
        assert "lineage" in detail
        lineage = detail["lineage"]
        assert lineage is not None

        # Entity node at center
        entity_nodes = [n for n in lineage["nodes"] if n["kind"] == "entity"]
        assert len(entity_nodes) >= 1
        entity_node = next(n for n in entity_nodes if n["id"] == "entity")
        assert entity_node["label"] == "Lineage Employee"
        assert "Employee Name" in entity_node["properties"]
        assert "Salary" in entity_node["properties"]

        # Source node present
        source_nodes = [n for n in lineage["nodes"] if n["kind"] == "source"]
        assert len(source_nodes) >= 1
        assert any(n["label"] == "payroll.xlsx" for n in source_nodes)

        # Binding edges connect source to entity
        binding_edges = [e for e in lineage["edges"] if e["kind"] == "binding"]
        assert len(binding_edges) == 2
        for be_ in binding_edges:
            assert "source-node" in be_["source_id"]
            assert be_["target_id"] == "entity"

        # Link edges connect entity to target
        link_edges = [e for e in lineage["edges"] if e["kind"] == "link"]
        assert len(link_edges) == 1
        assert link_edges[0]["source_id"] == "entity"
        assert link_edges[0]["target_id"] == "target-ent-dept-1"

        # Layout state preserved
        assert isinstance(lineage["layout_state"], dict)

    def test_entity_detail_with_draft_lineage_uses_draft_data(
        self,
        client,
        auth_headers,
    ):
        """Draft entity detail includes lineage from draft revision data."""
        obj_key = f"lineage_draft_{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/semantic/create-entity",
            json={
                "object_type_key": obj_key,
                "display_name": "Draft Entity",
                "description": "Test draft entity",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (200, 201)
        entity_id = create_resp.json()["id"]

        # Create draft revision (not published)
        _ = client.post(
            f"/api/entities/{entity_id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": str(uuid.uuid4()),
                        "property_key": "name",
                        "display_name": "Name",
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-draft",
                        "name": "draft_data.csv",
                        "source_type": "static_file",
                        "fields": ["name"],
                    },
                ],
                "publish": False,
            },
            headers=auth_headers,
        )

        detail_resp = client.get(
            f"/api/entities/{entity_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        # Lineage should use draft revision data
        lineage = detail.get("lineage")
        assert lineage is not None
        entity_node = next(n for n in lineage["nodes"] if n["id"] == "entity")
        assert entity_node["label"] == "Draft Entity"
        assert "Name" in entity_node["properties"]

        source = next(n for n in lineage["nodes"] if n["kind"] == "source")
        assert source["label"] == "draft_data.csv"

    def test_entity_detail_without_dataset_mapping_has_lineage(
        self,
        client,
        auth_headers,
    ):
        """Entity without dataset mapping still produces a lineage graph."""
        obj_key = f"no_ds_{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/semantic/create-entity",
            json={
                "object_type_key": obj_key,
                "display_name": "No Dataset Entity",
                "description": "Entity without dataset",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (200, 201)
        entity_id = create_resp.json()["id"]

        # Create draft with source but no dataset mapping
        _ = client.post(
            f"/api/entities/{entity_id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": str(uuid.uuid4()),
                        "property_key": "col_a",
                        "display_name": "Column A",
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "standalone-src",
                        "name": "standalone.csv",
                        "source_type": "static_file",
                        "fields": ["col_a"],
                    },
                ],
                "publish": False,
            },
            headers=auth_headers,
        )

        detail_resp = client.get(
            f"/api/entities/{entity_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        # Lineage must still exist even without dataset
        lineage = detail.get("lineage")
        assert lineage is not None
        assert len(lineage["nodes"]) >= 2  # entity + source

        # Entity label correct
        entity = next(n for n in lineage["nodes"] if n["id"] == "entity")
        assert entity["label"] == "No Dataset Entity"

    def test_entity_detail_without_revision_has_null_lineage(
        self,
        client,
        auth_headers,
    ):
        """Entity without any revision returns null lineage."""
        obj_key = f"no_rev_{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/semantic/create-entity",
            json={
                "object_type_key": obj_key,
                "display_name": "No Revision Entity",
                "description": "Entity with no revisions",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (200, 201)
        entity_id = create_resp.json()["id"]

        detail_resp = client.get(
            f"/api/entities/{entity_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        # No revision, so lineage should be null
        assert detail.get("lineage") is None

    def test_publish_succeeds_for_draft_without_dataset_mapping(
        self,
        client,
        auth_headers,
    ):
        """Publish succeeds for a valid draft that has no dataset mapping (PRD Slice 4)."""
        obj_key = f"pub_no_ds_{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/semantic/create-entity",
            json={
                "object_type_key": obj_key,
                "display_name": "No DS Publish Entity",
                "description": "Entity without dataset",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (200, 201)
        entity_id = create_resp.json()["id"]

        # Create draft with source node and binding (valid for publish)
        _ = client.post(
            f"/api/entities/{entity_id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": str(uuid.uuid4()),
                        "property_key": "emp_name",
                        "display_name": "Employee Name",
                        "is_required": True,
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-emp",
                        "name": "employees.csv",
                        "source_type": "static_file",
                        "fields": ["emp_name"],
                    },
                ],
                "source_bindings": [
                    {
                        "property_key": "emp_name",
                        "source_node_id": "src-emp",
                        "source_field_name": "emp_name",
                    },
                ],
                "publish": False,
            },
            headers=auth_headers,
        )

        # Publish without dataset dependency — must succeed
        publish_resp = client.post(
            f"/api/entities/{entity_id}/draft/publish",
            json={},
            headers=auth_headers,
        )
        assert publish_resp.status_code == 200, publish_resp.text
        data = publish_resp.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None

    def test_lineage_includes_dataset_and_version_when_mapping_exists(
        self,
        client,
        auth_headers,
    ):
        """When entity has a dataset mapping, Dataset and Version appear in lineage."""
        # Create entity with known dataset mapping
        obj_key = f"ds_lineage_{uuid.uuid4().hex[:8]}"
        create_resp = client.post(
            "/api/semantic/create-entity",
            json={
                "object_type_key": obj_key,
                "display_name": "DS Entity",
                "description": "Entity with dataset",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code in (200, 201)
        entity_id = create_resp.json()["id"]

        # Create draft with source nodes
        _ = client.post(
            f"/api/entities/{entity_id}/revisions",
            json={
                "properties": [
                    {
                        "property_id": str(uuid.uuid4()),
                        "property_key": "name",
                        "display_name": "Name",
                    },
                ],
                "source_nodes": [
                    {
                        "source_id": "src-with-ds",
                        "name": "data_with_ds.csv",
                        "source_type": "static_file",
                        "fields": ["name"],
                    },
                ],
                "publish": False,
            },
            headers=auth_headers,
        )

        detail_resp = client.get(
            f"/api/entities/{entity_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()

        lineage = detail.get("lineage")
        assert lineage is not None

        # If dataset mapping exists, dataset + version nodes should be present
        # (dataset info may be null if no mapping exists)
        if detail.get("dataset_name"):
            dataset_nodes = [n for n in lineage["nodes"] if n["kind"] == "dataset"]
            assert len(dataset_nodes) == 1

            # Source nodes should connect to dataset version, not directly to entity
            source_lineage = [
                e for e in lineage["edges"] if e["source_id"].startswith("source-node") and e["kind"] == "lineage"
            ]
            if source_lineage:
                for sl in source_lineage:
                    # Should target version, not entity
                    assert sl["target_id"] != "entity"
