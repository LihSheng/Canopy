import uuid

from v3.ingestion.domain import (
    LineageEdge,
    LineageEdgeType,
    LineageGraph,
    LineageNode,
    LineageNodeType,
    MappingDecision,
)


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
    if rename_map is None:
        rename_map = {}

    nodes: list[LineageNode] = []
    edges: list[LineageEdge] = []

    confirmed_mappings: dict[str, str] = {
        md.source_column_name: md.target_field_name
        for md in mapping_decisions if md.confirmed
    }

    file_node_id = f"file:{upload_id}"
    nodes.append(LineageNode(
        id=file_node_id,
        node_type=LineageNodeType.file,
        label=file_name,
        metadata={"upload_id": upload_id},
    ))

    sheet_node_id = f"sheet:{upload_id}"
    nodes.append(LineageNode(
        id=sheet_node_id,
        node_type=LineageNodeType.sheet,
        label=sheet_name,
        metadata={},
    ))
    edges.append(LineageEdge(
        id=str(uuid.uuid4()),
        from_node_id=sheet_node_id,
        to_node_id=file_node_id,
        edge_type=LineageEdgeType.derived_from,
        metadata={},
    ))

    raw_node_ids: dict[str, str] = {}
    for col in raw_columns:
        node_id = f"raw:{upload_id}:{col}"
        raw_node_ids[col] = node_id
        nodes.append(LineageNode(
            id=node_id,
            node_type=LineageNodeType.raw_column,
            label=col,
            metadata={},
        ))
        edges.append(LineageEdge(
            id=str(uuid.uuid4()),
            from_node_id=node_id,
            to_node_id=sheet_node_id,
            edge_type=LineageEdgeType.derived_from,
            metadata={},
        ))

    cleaned_fields: set[str] = set(normalized_fields.keys())
    for cleaned_name in rename_map:
        cleaned_fields.add(cleaned_name)

    cleaned_node_ids: dict[str, str] = {}
    for field in cleaned_fields:
        node_id = f"cleaned:{upload_id}:{field}"
        cleaned_node_ids[field] = node_id

        step_metadata: list[dict] = []
        for spec in step_specs:
            cols = _get_affected_columns(spec)
            if field in cols or rename_map.get(field, field) in cols:
                step_metadata.append({
                    "step_type": spec.get("step_type", ""),
                    "order": spec.get("order", 0),
                    "parameters": spec.get("parameters", {}),
                })

        nodes.append(LineageNode(
            id=node_id,
            node_type=LineageNodeType.cleaned_field,
            label=field,
            metadata={"cleaning_steps": step_metadata} if step_metadata else {},
        ))

        original_name = rename_map.get(field, field)
        src_node_id = raw_node_ids.get(original_name)
        if src_node_id:
            edges.append(LineageEdge(
                id=str(uuid.uuid4()),
                from_node_id=src_node_id,
                to_node_id=node_id,
                edge_type=LineageEdgeType.derived_from,
                metadata={"renamed": True} if original_name != field else {},
            ))

    onto_node_ids: dict[str, str] = {}
    for cleaned_field, onto_field in normalized_fields.items():
        node_id = f"onto:{upload_id}:{onto_field}"
        if node_id not in onto_node_ids:
            onto_node_ids[onto_field] = node_id
            nodes.append(LineageNode(
                id=node_id,
                node_type=LineageNodeType.ontology_field,
                label=onto_field,
                metadata={},
            ))

        src_node_id = cleaned_node_ids.get(cleaned_field)
        if src_node_id:
            edges.append(LineageEdge(
                id=str(uuid.uuid4()),
                from_node_id=src_node_id,
                to_node_id=node_id,
                edge_type=LineageEdgeType.normalized_to,
                metadata={},
            ))

    return LineageGraph(nodes=nodes, edges=edges)


def _get_affected_columns(spec: dict) -> list[str]:
    step_type = spec.get("step_type", "")
    params = spec.get("parameters", {})
    if step_type in ("trim", "parse_date", "normalize_nulls", "dedupe"):
        return params.get("columns", [])
    if step_type == "cast":
        return list(params.get("columns", {}).keys())
    if step_type == "rename":
        return list(params.get("mappings", {}).values())
    return []
