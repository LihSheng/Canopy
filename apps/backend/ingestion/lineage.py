from __future__ import annotations

import uuid

from ingestion.domain import (
    LineageEdge,
    LineageEdgeType,
    LineageGraph,
    LineageNode,
    LineageNodeType,
    MappingDecision,
)


def _get_affected_columns(step_specs: list[dict]) -> dict[str, list[dict]]:
    affected: dict[str, list[dict]] = {}
    for step in step_specs:
        params = step.get("parameters", {}) or {}
        columns = params.get("columns", [])
        if isinstance(columns, dict):
            columns = list(columns.keys())
        for column in columns:
            affected.setdefault(column, []).append(step)
    return affected


def build_lineage_graph(
    upload_id: str,
    file_name: str,
    sheet_name: str,
    raw_columns: list[str],
    step_specs: list[dict],
    mapping_decisions: list[MappingDecision],
    normalized_fields: dict[str, str],
    rename_map: dict[str, str] | None = None,
) -> LineageGraph:
    rename_map = rename_map or {}
    graph = LineageGraph()
    file_node = LineageNode(id=f"file:{uuid.uuid4()}", node_type=LineageNodeType.file, label=file_name)
    sheet_node = LineageNode(id=f"sheet:{uuid.uuid4()}", node_type=LineageNodeType.sheet, label=sheet_name)
    graph.nodes.extend([file_node, sheet_node])
    graph.edges.append(
        LineageEdge(
            id=str(uuid.uuid4()),
            from_node_id=sheet_node.id,
            to_node_id=file_node.id,
            edge_type=LineageEdgeType.derived_from,
        )
    )

    affected_columns = _get_affected_columns(step_specs)
    raw_nodes: dict[str, LineageNode] = {}
    cleaned_nodes: dict[str, LineageNode] = {}

    for column in raw_columns:
        raw_node = LineageNode(id=f"raw:{uuid.uuid4()}", node_type=LineageNodeType.raw_column, label=column)
        raw_nodes[column] = raw_node
        graph.nodes.append(raw_node)
        graph.edges.append(
            LineageEdge(
                id=str(uuid.uuid4()),
                from_node_id=raw_node.id,
                to_node_id=sheet_node.id,
                edge_type=LineageEdgeType.derived_from,
            )
        )

    for source_column, target_field in normalized_fields.items():
        cleaned_label = next((new for new, old in rename_map.items() if old == source_column), source_column)
        raw_source_column = rename_map.get(source_column, source_column)
        cleaned_node = LineageNode(
            id=f"cleaned:{uuid.uuid4()}",
            node_type=LineageNodeType.cleaned_field,
            label=cleaned_label,
            metadata={"cleaning_steps": list(affected_columns.get(source_column, []))},
        )
        cleaned_nodes[source_column] = cleaned_node
        graph.nodes.append(cleaned_node)

        raw_node = raw_nodes.get(raw_source_column)
        if raw_node is not None:
            graph.edges.append(
                LineageEdge(
                    id=str(uuid.uuid4()),
                    from_node_id=raw_node.id,
                    to_node_id=cleaned_node.id,
                    edge_type=LineageEdgeType.derived_from,
                    metadata={"renamed": source_column in rename_map},
                )
            )

        onto_node = LineageNode(
            id=f"onto:{uuid.uuid4()}",
            node_type=LineageNodeType.ontology_field,
            label=target_field,
        )
        graph.nodes.append(onto_node)
        graph.edges.append(
            LineageEdge(
                id=str(uuid.uuid4()),
                from_node_id=cleaned_node.id,
                to_node_id=onto_node.id,
                edge_type=LineageEdgeType.normalized_to,
            )
        )

    return graph

