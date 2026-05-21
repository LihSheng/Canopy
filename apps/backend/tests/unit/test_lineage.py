import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.unit

from common.database import Base
from connection.domain import Connection
from connection.repository import ConnectionRepository
from dataset.domain import Dataset, DatasetVersion
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetService
from ingestion.domain import (
    LineageEdgeType,
    LineageNodeType,
    MappingDecision,
)
from ingestion.lineage import build_lineage_graph
from run.domain import Run
from run.repository import RunRepository


@pytest.fixture(autouse=True)
def _setup_db():
    """Override conftest._setup_db to avoid PostgreSQL dependency."""
    yield


def _make_lineage_sqlite_session():
    engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
    import dataset.schema  # noqa: F401
    import connection.schema  # noqa: F401
    import run.schema  # noqa: F401
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


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


class TestDatasetLineageHandler:
    def test_includes_source_object_and_connection_nodes(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs", source_object_name="sheet1")
            DatasetRepository(session).save(dataset)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            node_types = {n["type"] for n in result["nodes"]}
            assert "source_object" in node_types
            assert "connection" in node_types
            assert "dataset" in node_types
        finally:
            session.close()

    def test_source_object_node_has_correct_label(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs", source_object_name="sheet1")
            DatasetRepository(session).save(dataset)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            source = [n for n in result["nodes"] if n["type"] == "source_object"][0]
            assert source["label"] == "sheet1"
        finally:
            session.close()

    def test_no_source_object_node_when_name_empty(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs", source_object_name="")
            DatasetRepository(session).save(dataset)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            node_types = {n["type"] for n in result["nodes"]}
            assert "source_object" not in node_types
        finally:
            session.close()

    def test_lineage_has_correct_node_types(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs", source_object_name="tbl")
            DatasetRepository(session).save(dataset)

            version_repo = DatasetVersionRepository(session)
            v = DatasetVersion(id="ver-1", dataset_id="ds-1", version_number=1)
            version_repo.save(v)

            run_repo = RunRepository(session)
            r = Run(id="run-1", project_id="proj-1", connection_id="conn-1", dataset_id="ds-1", status="completed")
            run_repo.save(r)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            node_types = {n["type"] for n in result["nodes"]}
            assert node_types == {"source_object", "connection", "dataset", "version", "run"}
        finally:
            session.close()

    def test_source_object_to_connection_edge_exists(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs", source_object_name="tbl")
            DatasetRepository(session).save(dataset)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            so_to_conn = [e for e in result["edges"] if e["from"].startswith("source_") and e["to"].startswith("connection_")]
            assert len(so_to_conn) == 1
            assert so_to_conn[0]["type"] == "feeds"
        finally:
            session.close()

    def test_connection_to_dataset_edge_exists(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs")
            DatasetRepository(session).save(dataset)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            conn_to_ds = [e for e in result["edges"] if e["from"].startswith("connection_") and e["to"].startswith("dataset_")]
            assert len(conn_to_ds) == 1
            assert conn_to_ds[0]["type"] == "provides"
        finally:
            session.close()

    def test_version_to_dataset_edge_exists(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs")
            DatasetRepository(session).save(dataset)

            version_repo = DatasetVersionRepository(session)
            version_repo.save(DatasetVersion(id="ver-1", dataset_id="ds-1", version_number=1))
            version_repo.save(DatasetVersion(id="ver-2", dataset_id="ds-1", version_number=2))

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            ver_to_ds = [e for e in result["edges"] if e["from"].startswith("version_") and e["to"].startswith("dataset_")]
            assert len(ver_to_ds) == 2
            for edge in ver_to_ds:
                assert edge["type"] == "belongs_to"
        finally:
            session.close()

    def test_run_to_dataset_edge_exists(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs")
            DatasetRepository(session).save(dataset)

            run_repo = RunRepository(session)
            run_repo.save(Run(
                id="run-1",
                project_id="proj-1",
                connection_id="conn-1",
                dataset_id="ds-1",
                status="completed",
            ))
            run_repo.save(Run(
                id="run-2",
                project_id="proj-1",
                connection_id="conn-1",
                dataset_id="ds-1",
                status="failed",
            ))

            result = DatasetService(
                DatasetRepository(session),
                DatasetVersionRepository(session),
            ).get_lineage("ds-1")

            run_to_ds = [e for e in result["edges"] if e["from"].startswith("run_") and e["to"].startswith("dataset_")]
            assert len(run_to_ds) == 2
            for edge in run_to_ds:
                assert edge["type"] == "produces"
        finally:
            session.close()

    def test_version_node_label_includes_version_number(self):
        session = _make_lineage_sqlite_session()
        try:
            conn = Connection(id="conn-1", project_id="proj-1", source_type="static_file", name="MyConn")
            ConnectionRepository(session).save(conn)

            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="conn-1", name="MyDs")
            DatasetRepository(session).save(dataset)

            version_repo = DatasetVersionRepository(session)
            version_repo.save(DatasetVersion(id="ver-1", dataset_id="ds-1", version_number=3))

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            version_nodes = [n for n in result["nodes"] if n["type"] == "version"]
            assert len(version_nodes) == 1
            assert version_nodes[0]["label"] == "v3"
        finally:
            session.close()

    def test_dataset_not_found_raises_error(self):
        session = _make_lineage_sqlite_session()
        try:
            from common.errors import NotFoundError
            with pytest.raises(NotFoundError, match="Dataset not found"):
                DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("no-such-ds")
        finally:
            session.close()

    def test_no_connection_edges_when_connection_missing(self):
        session = _make_lineage_sqlite_session()
        try:
            dataset = Dataset(id="ds-1", project_id="proj-1", connection_id="bad-conn", name="MyDs", source_object_name="tbl")
            DatasetRepository(session).save(dataset)

            result = DatasetService(DatasetRepository(session), DatasetVersionRepository(session)).get_lineage("ds-1")

            node_types = {n["type"] for n in result["nodes"]}
            assert "connection" not in node_types

            feeds_edges = [e for e in result["edges"] if e["type"] == "feeds"]
            provides_edges = [e for e in result["edges"] if e["type"] == "provides"]
            assert len(feeds_edges) == 0
            assert len(provides_edges) == 0
        finally:
            session.close()

