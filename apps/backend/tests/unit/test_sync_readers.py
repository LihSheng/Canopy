from datetime import datetime

import pytest

from sync.readers._source_models import (
    SourceBase,
    SourceBudgetCodeRow,
    SourceClaimRow,
    SourceCostCenterRow,
    SourceDepartmentRow,
    SourceEmployeeRow,
    SourcePayrollRow,
)
from sync.readers.budget_codes import BudgetCodeReader
from sync.readers.claims import ClaimReader
from sync.readers.cost_centers import CostCenterReader
from sync.readers.departments import DepartmentReader
from sync.readers.employees import EmployeeReader
from sync.readers.payroll import PayrollReader
from tests.unit.postgres_test_db import make_postgres_session

pytestmark = pytest.mark.business_rule


def _source_db_with_rows(engine, *row_lists):
    SourceBase.metadata.drop_all(bind=engine)
    SourceBase.metadata.create_all(bind=engine)
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        for rows in row_lists:
            session.add_all(rows)
        session.commit()
    return engine


class TestDepartmentReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceDepartmentRow(source_key="D001", name="Engineering"),
                SourceDepartmentRow(source_key="D002", name="Marketing"),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = DepartmentReader()
            result = reader.read(source_db)

        assert len(result) == 2
        assert result[0].source_key == "D001"
        assert result[0].name == "Engineering"
        assert result[0].parent_key is None
        assert result[0].status == "active"

    def test_empty_table_returns_empty_list(self, source_engine):
        engine = _source_db_with_rows(source_engine)
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = DepartmentReader()
            result = reader.read(source_db)

        assert result == []

    def test_entity_type(self):
        assert DepartmentReader().entity_type == "departments"


class TestEmployeeReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceEmployeeRow(
                    source_key="E001",
                    full_name="Alice Tan",
                    department_key="D001",
                    cost_center_key="CC01",
                ),
                SourceEmployeeRow(
                    source_key="E002",
                    full_name="Bob Lim",
                    department_key="D002",
                ),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = EmployeeReader()
            result = reader.read(source_db)

        assert len(result) == 2
        assert result[0].source_key == "E001"
        assert result[0].cost_center_key == "CC01"
        assert result[1].cost_center_key is None


class TestClaimReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceClaimRow(
                    source_key="C001",
                    employee_key="E001",
                    department_key="D001",
                    amount=150.0,
                    currency="MYR",
                    claim_type="travel",
                    submitted_at="2025-01-15T10:00:00",
                    status="approved",
                ),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = ClaimReader()
            result = reader.read(source_db)

        assert len(result) == 1
        assert result[0].amount == 150.0
        assert result[0].claim_type == "travel"
        assert isinstance(result[0].submitted_at, datetime)

    def test_empty_table(self, source_engine):
        engine = _source_db_with_rows(source_engine)
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = ClaimReader()
            result = reader.read(source_db)

        assert result == []


class TestPayrollReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourcePayrollRow(
                    source_key="P001",
                    employee_key="E001",
                    department_key="D001",
                    amount=5000.0,
                    currency="MYR",
                    period_start="2025-01",
                    period_end="2025-01",
                ),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = PayrollReader()
            result = reader.read(source_db)

        assert len(result) == 1
        assert result[0].amount == 5000.0
        assert result[0].period_start == "2025-01"


class TestCostCenterReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceCostCenterRow(source_key="CC001", name="R&D", department_key="D001"),
                SourceCostCenterRow(source_key="CC002", name="Admin"),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = CostCenterReader()
            result = reader.read(source_db)

        assert len(result) == 2
        assert result[0].name == "R&D"
        assert result[1].department_key is None


class TestBudgetCodeReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceBudgetCodeRow(source_key="B001", name="Opex-IT", department_key="D001"),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = BudgetCodeReader()
            result = reader.read(source_db)

        assert len(result) == 1
        assert result[0].name == "Opex-IT"


class TestSourceDatabaseManager:
    """Cover _SourceDatabaseManager lazy init and set/reset (source_db.py lines 15-43, 52-65)."""

    def test_source_engine_lazy_init(self):
        """line 23-26: engine created on first access."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        eng = mgr.source_engine()
        assert eng is not None
        # second call returns cached
        assert mgr.source_engine() is eng

    def test_source_session_factory_lazy_init(self):
        """line 28-33: session factory created on first access."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        factory = mgr.source_session_factory()
        assert factory is not None

    def test_set_source_engine(self):
        """lines 35-39: set_source_engine replaces engine."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        handle = make_postgres_session(())
        try:
            mgr.set_source_engine(handle.engine)
            assert mgr.source_engine() is handle.engine
        finally:
            handle.close()

    def test_reset_source_engine(self):
        """lines 41-43: reset clears cache."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        _ = mgr.source_engine()  # trigger lazy init
        mgr.reset_source_engine()
        # After reset, a new call creates new engine
        eng2 = mgr.source_engine()
        assert eng2 is not None

    def test_public_source_engine_function(self):
        """line 52-53: source_engine() public function."""
        from sync.source_db import source_engine

        e = source_engine()
        assert e is not None

    def test_public_source_session_factory(self):
        """line 56-57: source_session_factory() public function."""
        from sync.source_db import source_session_factory

        f = source_session_factory()
        assert f is not None

    def test_public_set_source_engine(self):
        """line 60-61: set_source_engine() public function."""
        from sync.source_db import set_source_engine

        handle = make_postgres_session(())
        try:
            set_source_engine(handle.engine)
        finally:
            handle.close()

    def test_public_reset_source_engine(self):
        """line 64-65: reset_source_engine() public function."""
        from sync.source_db import reset_source_engine

        reset_source_engine()


class TestBuildSourceEngine:
    """Cover _build_source_engine edge cases (source_db.py line 20)."""

    def test_memory_url_uses_static_pool(self):
        """line 20: SQLite :memory: URL uses StaticPool."""
        from sqlalchemy.pool import StaticPool

        from common.config import settings
        from sync.source_db import _SourceDatabaseManager

        original_url = settings.source_database_url
        try:
            settings.source_database_url = "sqlite:///:memory:"
            mgr = _SourceDatabaseManager()
            # Reset internal state so _build_source_engine is called fresh
            mgr._source_engine = None
            eng = mgr.source_engine()
            assert isinstance(eng.pool, StaticPool)
        finally:
            settings.source_database_url = original_url


@pytest.mark.asyncio
class TestMysqlCdcReader:
    """Cover mysql_cdc_reader.py basic methods."""

    async def test_init_sets_attributes(self):
        """lines 21-24: __init__ sets attributes."""
        from sync.readers.mysql_cdc_reader import MysqlCdcReader

        reader = MysqlCdcReader({"host": "localhost"}, "ds-1", "test_table")
        assert reader.config == {"host": "localhost"}
        assert reader.dataset_id == "ds-1"
        assert reader.table_name == "test_table"
        assert reader.running is False

    async def test_stop_sets_running_false(self):
        """line 156: stop sets running to False."""
        from sync.readers.mysql_cdc_reader import MysqlCdcReader

        reader = MysqlCdcReader({}, "ds-1", "tbl")
        reader.running = True
        reader.stop()
        assert reader.running is False

    async def test_run_simulation_writes_initial_event(self):
        """lines 114-128: _run_simulation writes initial event."""
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        from sync.readers.mysql_cdc_reader import MysqlCdcReader

        reader = MysqlCdcReader({}, "ds-1", "tbl")
        reader.running = False  # prevent infinite loop

        mock_on_event = MagicMock()
        mock_file = MagicMock()

        with patch("builtins.open", return_value=mock_file):
            await reader._run_simulation(Path("/tmp/test.jsonl"), mock_on_event)

        assert mock_file.__enter__.return_value.write.called
        assert mock_on_event.called


@pytest.mark.asyncio
class TestPostgresCdcReader:
    """Cover pg_cdc_reader.py basic methods."""

    async def test_init_sets_attributes(self):
        """lines 23-26: __init__ sets attributes."""
        from sync.readers.pg_cdc_reader import PostgresCdcReader

        reader = PostgresCdcReader({"host": "localhost"}, "ds-1", "test_table")
        assert reader.config == {"host": "localhost"}
        assert reader.dataset_id == "ds-1"
        assert reader.table_name == "test_table"
        assert reader.running is False

    async def test_stop_sets_running_false(self):
        """line 156: stop sets running to False."""
        from sync.readers.pg_cdc_reader import PostgresCdcReader

        reader = PostgresCdcReader({}, "ds-1", "tbl")
        reader.running = True
        reader.stop()
        assert reader.running is False

    async def test_run_simulation_writes_initial_event(self):
        """lines 114-128: _run_simulation writes initial event."""
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        from sync.readers.pg_cdc_reader import PostgresCdcReader

        reader = PostgresCdcReader({}, "ds-1", "tbl")
        reader.running = False  # prevent infinite loop

        mock_on_event = MagicMock()
        mock_file = MagicMock()

        with patch("builtins.open", return_value=mock_file):
            await reader._run_simulation(Path("/tmp/test.jsonl"), mock_on_event)

        assert mock_file.__enter__.return_value.write.called
        assert mock_on_event.called
