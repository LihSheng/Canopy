import pytest

pytestmark = pytest.mark.unit

import uuid

from ingestion.domain import (
    LineageEdgeType,
    LineageNodeType,
    MappingDecision,
)
from ingestion.lineage import build_lineage_graph


_UPLOAD_ID = "test-upload-1"


def _make_decisions(pairs: list[tuple[str, str]]) -> list[MappingDecision]:
    return [
        MappingDecision(source_column_name=s, target_field_name=t, confirmed=True, overridden_by_user=False)
        for s, t in pairs
    ]


class TestBuildLineageGraph:
    def test_creates_file_node(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={},
        )
        file_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.file]
        assert len(file_nodes) == 1
        assert file_nodes[0].label == "payroll.xlsx"

    def test_creates_sheet_node(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={},
        )
        sheet_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.sheet]
        assert len(sheet_nodes) == 1
        assert sheet_nodes[0].label == "Data"

    def test_creates_raw_column_nodes(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount", "date"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={},
        )
        raw_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.raw_column]
        assert len(raw_nodes) == 3
        assert {n.label for n in raw_nodes} == {"name", "amount", "date"}

    def test_creates_cleaned_field_nodes(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={"name": "employee_name", "amount": "salary"},
        )
        cleaned_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.cleaned_field]
        assert len(cleaned_nodes) == 2
        assert {n.label for n in cleaned_nodes} == {"name", "amount"}

    def test_creates_ontology_field_nodes(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={"name": "employee_name", "amount": "salary"},
        )
        onto_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.ontology_field]
        assert len(onto_nodes) == 2
        assert {n.label for n in onto_nodes} == {"employee_name", "salary"}

    def test_edge_counts(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={"name": "employee_name", "amount": "salary"},
        )
        derived = [e for e in graph.edges if e.edge_type == LineageEdgeType.derived_from]
        normalized = [e for e in graph.edges if e.edge_type == LineageEdgeType.normalized_to]
        assert len(derived) == 5  # 1 sheet->file + 2 raw->sheet + 2 raw->cleaned
        assert len(normalized) == 2  # 2 cleaned->onto

    def test_edge_types_correct(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={"name": "employee_name"},
        )
        edge_types = {e.edge_type for e in graph.edges}
        assert LineageEdgeType.derived_from in edge_types
        assert LineageEdgeType.normalized_to in edge_types

    def test_node_count_total(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["col_a", "col_b", "col_c"],
            step_specs=[],
            mapping_decisions=_make_decisions([("col_a", "field_a"), ("col_b", "field_b")]),
            normalized_fields={"col_a": "field_a", "col_b": "field_b"},
        )
        assert len(graph.nodes) == 9  # 1 file + 1 sheet + 3 raw + 2 cleaned + 2 onto
        assert len(graph.edges) == 8  # 1 sheet->file + 3 raw->sheet + 2 raw->cleaned + 2 cleaned->onto

    def test_rename_map_updates_cleaned_field_labels(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["old_name"],
            step_specs=[],
            mapping_decisions=_make_decisions([("old_name", "employee_name")]),
            normalized_fields={"new_name": "employee_name"},
            rename_map={"new_name": "old_name"},
        )
        raw_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.raw_column]
        assert raw_nodes[0].label == "old_name"
        cleaned_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.cleaned_field]
        assert cleaned_nodes[0].label == "new_name"

    def test_metadata_on_cleaned_field_reflects_steps(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount"],
            step_specs=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}},
                {"step_type": "cast", "order": 1, "parameters": {"columns": {"amount": "number"}}},
            ],
            mapping_decisions=[],
            normalized_fields={"name": "employee_name", "amount": "salary"},
        )
        cleaned_nodes = {n.label: n for n in graph.nodes if n.node_type == LineageNodeType.cleaned_field}
        name_steps = cleaned_nodes["name"].metadata.get("cleaning_steps", [])
        assert len(name_steps) == 1
        assert name_steps[0]["step_type"] == "trim"

        amount_steps = cleaned_nodes["amount"].metadata.get("cleaning_steps", [])
        assert len(amount_steps) == 1
        assert amount_steps[0]["step_type"] == "cast"

    def test_empty_raw_columns(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="empty.xlsx",
            sheet_name="Data",
            raw_columns=[],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={},
        )
        assert len(graph.nodes) == 2  # file + sheet only
        assert len(graph.edges) == 1  # sheet -> file only

    def test_no_mapping_decisions(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name", "amount"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={},
        )
        onto_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.ontology_field]
        assert len(onto_nodes) == 0
        normalized_edges = [e for e in graph.edges if e.edge_type == LineageEdgeType.normalized_to]
        assert len(normalized_edges) == 0

    def test_sheet_to_file_edge_direction(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={},
        )
        sheet_file_edges = [
            e for e in graph.edges
            if e.from_node_id.startswith("sheet:") and e.to_node_id.startswith("file:")
        ]
        assert len(sheet_file_edges) == 1

    def test_raw_column_to_cleaned_edge_present(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name"],
            step_specs=[],
            mapping_decisions=_make_decisions([("name", "employee_name")]),
            normalized_fields={"name": "employee_name"},
        )
        raw_cleaned_edges = [
            e for e in graph.edges
            if e.from_node_id.startswith("raw:") and e.to_node_id.startswith("cleaned:")
        ]
        assert len(raw_cleaned_edges) >= 1

    def test_normalized_edge_points_to_ontology(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name"],
            step_specs=[],
            mapping_decisions=_make_decisions([("name", "employee_name")]),
            normalized_fields={"name": "employee_name"},
        )
        norm_edges = [
            e for e in graph.edges
            if e.from_node_id.startswith("cleaned:") and e.to_node_id.startswith("onto:")
        ]
        assert len(norm_edges) == 1

    def test_rename_edge_metadata(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["old_col"],
            step_specs=[],
            mapping_decisions=_make_decisions([("old_col", "field")]),
            normalized_fields={"new_col": "field"},
            rename_map={"new_col": "old_col"},
        )
        rename_edges = [
            e for e in graph.edges
            if e.from_node_id.startswith("raw:") and e.to_node_id.startswith("cleaned:")
        ]
        assert len(rename_edges) == 1
        assert rename_edges[0].metadata.get("renamed") is True

    def test_multiple_cleaned_fields_same_raw_column(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="payroll.xlsx",
            sheet_name="Data",
            raw_columns=["name"],
            step_specs=[],
            mapping_decisions=[],
            normalized_fields={"name": "full_name"},
        )
        cleaned_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.cleaned_field]
        onto_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.ontology_field]
        assert len(cleaned_nodes) == 1
        assert len(onto_nodes) == 1

    def test_graph_with_no_steps_and_full_mapping(self):
        graph = build_lineage_graph(
            upload_id=_UPLOAD_ID,
            file_name="data.csv",
            sheet_name="Sheet1",
            raw_columns=["a", "b", "c"],
            step_specs=[],
            mapping_decisions=_make_decisions([("a", "x"), ("b", "y"), ("c", "z")]),
            normalized_fields={"a": "x", "b": "y", "c": "z"},
        )
        raw_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.raw_column]
        cleaned_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.cleaned_field]
        onto_nodes = [n for n in graph.nodes if n.node_type == LineageNodeType.ontology_field]
        assert len(raw_nodes) == 3
        assert len(cleaned_nodes) == 3
        assert len(onto_nodes) == 3

