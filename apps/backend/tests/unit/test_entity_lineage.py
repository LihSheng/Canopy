"""Unit tests for the entity lineage graph builder.

Verifies the generic lineage graph contract per PRD 0021:
- Entity at center
- Dataset / Dataset Version as upstream context
- Source nodes feed into Dataset Version
- Property labels on Entity node
- Binding edges for source-field-to-property
- Link edges for entity-to-entity relationships
- Works without dataset info (draft-only)
"""

import pytest

from entity_lineage.domain import (
    LineageEdgeKind,
    LineageNodeKind,
)
from entity_lineage.graph_builder import build_entity_lineage_graph
from entity_revision.domain import EntityProperty, EntityRevision, SourceBinding

pytestmark = pytest.mark.unit


def _make_revision(
    entity_id: str = "ent-1",
    properties: list[EntityProperty] | None = None,
    source_bindings: list[SourceBinding] | None = None,
    source_nodes: list[dict] | None = None,
    links: list[dict] | None = None,
    layout_state: dict | None = None,
) -> EntityRevision:
    return EntityRevision(
        id="rev-1",
        entity_id=entity_id,
        revision_number=1,
        status="published",
        properties=properties or [],
        source_bindings=source_bindings or [],
        source_nodes=source_nodes or [],
        links=links or [],
        layout_state=layout_state or {},
    )


class TestBuildEntityLineageGraph:
    """Graph builder contract tests — verify the read model shape."""

    # ── Entity as center ──────────────────────────────────────────────────

    def test_entity_node_is_always_present(self):
        """The Entity must always appear as a node, even with no extra data."""
        rev = _make_revision(entity_id="ent-1")
        graph = build_entity_lineage_graph(rev, entity_label="Employee")

        entity_nodes = [n for n in graph.nodes if n.kind == LineageNodeKind.ENTITY]
        assert len(entity_nodes) == 1
        assert entity_nodes[0].id == "entity"
        assert entity_nodes[0].label == "Employee"

    def test_entity_node_includes_property_labels(self):
        """Entity properties appear as labels on the Entity node."""
        rev = _make_revision(
            entity_id="ent-1",
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="name",
                    display_name="Full Name",
                    semantic_type="string",
                    is_required=True,
                ),
                EntityProperty(
                    property_id="p2",
                    property_key="salary",
                    display_name="Salary",
                    semantic_type="number",
                ),
            ],
        )
        graph = build_entity_lineage_graph(rev, entity_label="Employee")

        entity = next(n for n in graph.nodes if n.kind == LineageNodeKind.ENTITY)
        assert "Full Name" in entity.properties
        assert "Salary" in entity.properties

    # ── Dataset / Version as upstream context ─────────────────────────────

    def test_dataset_and_version_nodes_when_dataset_info_provided(self):
        """Dataset and Dataset Version appear as upstream context nodes."""
        rev = _make_revision(entity_id="ent-1")
        graph = build_entity_lineage_graph(
            rev,
            entity_label="Employee",
            dataset_id="ds-1",
            dataset_name="HR Master",
            dataset_version_id="dv-1",
            dataset_version_label="v3",
        )

        ds_nodes = [n for n in graph.nodes if n.kind == LineageNodeKind.DATASET]
        assert len(ds_nodes) == 1
        assert ds_nodes[0].id == "dataset"
        assert ds_nodes[0].label == "HR Master"

        dv_nodes = [n for n in graph.nodes if n.kind == LineageNodeKind.DERIVED and n.subtype == "dataset_version"]
        # Dataset Version is represented as a derived node with subtype
        assert len(dv_nodes) >= 1

    def test_dataset_to_version_to_entity_lineage_edges(self):
        """Dataset connects to Dataset Version, which connects to Entity."""
        rev = _make_revision(entity_id="ent-1")
        graph = build_entity_lineage_graph(
            rev,
            entity_label="Employee",
            dataset_id="ds-1",
            dataset_name="HR Master",
            dataset_version_id="dv-1",
            dataset_version_label="v3",
        )

        lineage_edges = [e for e in graph.edges if e.kind == LineageEdgeKind.LINEAGE]
        assert len(lineage_edges) >= 2  # dataset->version, version->entity

        # Find dataset->version edge
        ds_to_ver = [e for e in lineage_edges if e.source_id == "dataset"]
        assert len(ds_to_ver) == 1

        # Find version->entity edge
        ver_to_ent = [e for e in lineage_edges if e.target_id == "entity"]
        assert len(ver_to_ent) >= 1

    # ── Source nodes feed into Dataset Version ────────────────────────────

    def test_source_nodes_connect_to_dataset_version(self):
        """Source nodes connect into Dataset Version, not directly into Entity."""
        rev = _make_revision(
            entity_id="ent-1",
            source_nodes=[
                {
                    "source_id": "src-1",
                    "name": "employees.csv",
                    "source_type": "static_file",
                    "fields": ["name", "salary", "dept"],
                },
            ],
        )
        graph = build_entity_lineage_graph(
            rev,
            entity_label="Employee",
            dataset_id="ds-1",
            dataset_name="HR Master",
            dataset_version_id="dv-1",
            dataset_version_label="v3",
        )

        source_nodes = [n for n in graph.nodes if n.kind == LineageNodeKind.SOURCE]
        assert len(source_nodes) == 1
        assert source_nodes[0].label == "employees.csv"

        # Source should connect to dataset-version, NOT directly to entity
        source_edges = [e for e in graph.edges if e.source_id == "source-node-src-1"]
        assert len(source_edges) >= 1
        for edge in source_edges:
            if edge.kind == LineageEdgeKind.LINEAGE:
                # Source lineage edges go to dataset-version
                assert "dv" in edge.target_id.lower() or "version" in edge.target_id.lower()

    def test_graph_without_dataset_info_still_renders(self):
        """Draft entity without dataset binding still produces a valid graph."""
        rev = _make_revision(
            entity_id="ent-1",
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="name",
                    display_name="Name",
                ),
            ],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "name": "payroll.xlsx",
                    "source_type": "static_file",
                    "fields": ["name"],
                },
            ],
        )
        graph = build_entity_lineage_graph(rev, entity_label="Employee")

        # Should have entity + source nodes
        assert len(graph.nodes) >= 2
        entity = next(n for n in graph.nodes if n.kind == LineageNodeKind.ENTITY)
        assert entity.label == "Employee"

        # Source nodes still present
        sources = [n for n in graph.nodes if n.kind == LineageNodeKind.SOURCE]
        assert len(sources) == 1

    # ── Binding edges (source-field-to-property) ─────────────────────────

    def test_binding_edges_for_each_source_property_mapping(self):
        """Each source binding creates a binding edge from source field to entity property."""
        rev = _make_revision(
            entity_id="ent-1",
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="name",
                    display_name="Full Name",
                ),
                EntityProperty(
                    property_id="p2",
                    property_key="salary",
                    display_name="Salary",
                ),
            ],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "name": "employees.csv",
                    "source_type": "static_file",
                    "fields": ["name", "salary"],
                },
            ],
            source_bindings=[
                SourceBinding(
                    property_key="name",
                    source_node_id="src-1",
                    source_field_name="name",
                ),
                SourceBinding(
                    property_key="salary",
                    source_node_id="src-1",
                    source_field_name="salary",
                ),
            ],
        )
        graph = build_entity_lineage_graph(
            rev,
            entity_label="Employee",
            dataset_id="ds-1",
            dataset_name="HR Master",
            dataset_version_id="dv-1",
            dataset_version_label="v3",
        )

        binding_edges = [e for e in graph.edges if e.kind == LineageEdgeKind.BINDING]
        assert len(binding_edges) == 2
        # Each binding should go from source-node to entity
        for be_ in binding_edges:
            assert "source-node" in be_.source_id
            assert be_.target_id == "entity"

    # ── Link edges (entity-to-entity) ────────────────────────────────────

    def test_entity_links_become_link_edges(self):
        """Entity-to-Entity links render as link edges."""
        rev = _make_revision(
            entity_id="ent-1",
            links=[
                {
                    "link_id": "link-1",
                    "display_name": "works_for",
                    "source_property_key": "dept_id",
                    "target_object_type_id": "ent-dept",
                    "target_property_key": "id",
                    "cardinality": "many_to_one",
                },
            ],
        )
        graph = build_entity_lineage_graph(rev, entity_label="Employee")

        link_edges = [e for e in graph.edges if e.kind == LineageEdgeKind.LINK]
        assert len(link_edges) == 1
        assert link_edges[0].source_id == "entity"
        assert link_edges[0].target_id == "target-ent-dept"

    def test_link_creates_target_entity_node(self):
        """Each link creates a target entity node."""
        rev = _make_revision(
            entity_id="ent-1",
            links=[
                {
                    "link_id": "link-1",
                    "display_name": "works_for",
                    "source_property_key": "dept_id",
                    "target_object_type_id": "ent-dept",
                    "target_property_key": "id",
                    "cardinality": "many_to_one",
                },
            ],
        )
        graph = build_entity_lineage_graph(rev, entity_label="Employee")

        # target node should exist
        target_nodes = [n for n in graph.nodes if n.id == "target-ent-dept"]
        assert len(target_nodes) == 1
        assert target_nodes[0].kind == LineageNodeKind.ENTITY
        assert target_nodes[0].label == "works_for"

    # ── Layout state preservation ─────────────────────────────────────────

    def test_layout_state_preserved_in_graph(self):
        """Layout state from the revision is carried into the graph."""
        layout = {"entity": {"x": 100, "y": 200}}
        rev = _make_revision(entity_id="ent-1", layout_state=layout)
        graph = build_entity_lineage_graph(rev, entity_label="Employee")

        assert graph.layout_state == layout

    # ── Derived nodes ─────────────────────────────────────────────────────

    def test_derived_nodes_rendered_when_present_in_stored_data(self):
        """Derived nodes from the revision source_nodes (with kind=derived) render."""
        rev = _make_revision(
            entity_id="ent-1",
            source_nodes=[
                {
                    "source_id": "derived-1",
                    "name": "Cleaned Employee",
                    "source_type": "derived",
                    "kind": "derived",
                    "fields": ["name", "salary"],
                },
                {
                    "source_id": "src-1",
                    "name": "raw_employees.csv",
                    "source_type": "static_file",
                    "fields": ["raw_name", "raw_salary"],
                },
            ],
        )
        graph = build_entity_lineage_graph(
            rev,
            entity_label="Employee",
            dataset_id="ds-1",
            dataset_name="HR Master",
            dataset_version_id="dv-1",
            dataset_version_label="v3",
        )

        derived = [n for n in graph.nodes if n.kind == LineageNodeKind.DERIVED]
        assert len(derived) >= 1
        assert any(n.label == "Cleaned Employee" for n in derived)
