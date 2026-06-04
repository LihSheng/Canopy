"""Entity lineage graph builder.

Constructs an entity-centered lineage graph from an EntityRevision and
optional dataset/version context.

The graph follows the PRD 0021 contract:
- Entity at center with property labels
- Dataset and Dataset Version as upstream nodes
- Source nodes feed into Dataset Version via lineage edges
- Source-field-to-property bindings are binding edges
- Entity-to-entity links are link edges
- Derived nodes rendered when present in stored data
"""

from entity_lineage.domain import (
    EntityLineageGraph,
    LineageEdge,
    LineageEdgeKind,
    LineageNode,
    LineageNodeKind,
)
from entity_revision.domain import EntityRevision


def build_entity_lineage_graph(
    revision: EntityRevision,
    entity_label: str,
    dataset_id: str | None = None,
    dataset_name: str | None = None,
    dataset_version_id: str | None = None,
    dataset_version_label: str | None = None,
) -> EntityLineageGraph:
    """Build an entity-centered lineage graph from a revision.

    The graph centers the Entity node, places Dataset and Dataset Version
    as upstream context, connects source nodes into the Version, and
    renders derived nodes, binding edges, and link edges.

    Args:
        revision: The entity revision (draft or published).
        entity_label: Display label for the Entity node.
        dataset_id: Optional backing dataset ID.
        dataset_name: Optional backing dataset display name.
        dataset_version_id: Optional active dataset version ID.
        dataset_version_label: Optional dataset version label (e.g. "v3").

    Returns:
        An EntityLineageGraph read model.
    """
    nodes: list[LineageNode] = []
    edges: list[LineageEdge] = []

    # ── Entity node (center) ────────────────────────────────────────────
    property_labels = [p.display_name for p in (revision.properties or [])]
    nodes.append(
        LineageNode(
            id="entity",
            kind=LineageNodeKind.ENTITY,
            label=entity_label,
            properties=property_labels,
        )
    )

    # ── Source and derived nodes ────────────────────────────────────────
    source_nodes = revision.source_nodes or []
    has_dataset_context = bool(dataset_id)

    for sn in source_nodes:
        source_id_val = sn.get("source_id", "")
        node_id = f"source-node-{source_id_val}"
        source_type = sn.get("source_type", "")
        kind_raw = sn.get("kind", "")

        # Determine node kind
        if kind_raw == "derived" or source_type == "derived":
            kind = LineageNodeKind.DERIVED
        else:
            kind = LineageNodeKind.SOURCE

        nodes.append(
            LineageNode(
                id=node_id,
                kind=kind,
                label=sn.get("name", source_id_val),
                subtype="dataset_version" if node_id == "dataset-version" else "",
            )
        )

        if has_dataset_context:
            # Source → Dataset Version (lineage), not directly to Entity
            edges.append(
                LineageEdge(
                    id=f"{node_id}-to-dv",
                    kind=LineageEdgeKind.LINEAGE,
                    source_id=node_id,
                    target_id="dataset-version",
                )
            )
        else:
            # No dataset context: connect source directly to entity with lineage edge
            edges.append(
                LineageEdge(
                    id=f"{node_id}-to-entity",
                    kind=LineageEdgeKind.LINEAGE,
                    source_id=node_id,
                    target_id="entity",
                )
            )

    # ── Dataset and Dataset Version nodes ───────────────────────────────
    if has_dataset_context and dataset_name:
        nodes.append(
            LineageNode(
                id="dataset",
                kind=LineageNodeKind.DATASET,
                label=dataset_name,
            )
        )
        # Dataset Version node
        version_label = dataset_version_label or "Active Version"
        dv_node_id = "dataset-version"
        nodes.append(
            LineageNode(
                id=dv_node_id,
                kind=LineageNodeKind.DERIVED,
                label=version_label,
                subtype="dataset_version",
            )
        )
        # Dataset → Dataset Version (lineage)
        edges.append(
            LineageEdge(
                id="dataset-to-dv",
                kind=LineageEdgeKind.LINEAGE,
                source_id="dataset",
                target_id=dv_node_id,
            )
        )
        # Dataset Version → Entity (lineage)
        edges.append(
            LineageEdge(
                id="dv-to-entity",
                kind=LineageEdgeKind.LINEAGE,
                source_id=dv_node_id,
                target_id="entity",
            )
        )

    # ── Binding edges (source-field → entity property) ──────────────────
    for b in revision.source_bindings or []:
        source_node_id = f"source-node-{b.source_node_id}"
        edges.append(
            LineageEdge(
                id=f"{source_node_id}-bind-{b.property_key}",
                kind=LineageEdgeKind.BINDING,
                source_id=source_node_id,
                target_id="entity",
                label=b.source_field_name,
                source_handle=b.source_field_name,
                target_handle=b.property_key,
            )
        )

    # ── Link edges (entity → linked entity) ─────────────────────────────
    for link in revision.links or []:
        target_id = link.get("target_object_type_id", "")
        target_node_id = f"target-{target_id}"
        display_name = link.get("display_name", target_id)

        # Target entity node
        nodes.append(
            LineageNode(
                id=target_node_id,
                kind=LineageNodeKind.ENTITY,
                label=display_name,
                properties=[],
            )
        )
        # Link edge
        edges.append(
            LineageEdge(
                id=f"entity-link-{target_id}",
                kind=LineageEdgeKind.LINK,
                source_id="entity",
                target_id=target_node_id,
                label=display_name,
            )
        )

    return EntityLineageGraph(
        entity_id=revision.entity_id,
        entity_label=entity_label,
        nodes=nodes,
        edges=edges,
        layout_state=revision.layout_state or {},
    )
