import pytest

from datetime import datetime

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
            ]
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
            ]
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
            ]
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
            ]
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
                SourceCostCenterRow(
                    source_key="CC001", name="R&D", department_key="D001"
                ),
                SourceCostCenterRow(
                    source_key="CC002", name="Admin"
                ),
            ]
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
                SourceBudgetCodeRow(
                    source_key="B001", name="Opex-IT", department_key="D001"
                ),
            ]
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
        from sqlalchemy import create_engine
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        eng = create_engine("sqlite://")
        mgr.set_source_engine(eng)
        assert mgr.source_engine() is eng

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
        from sqlalchemy import create_engine
        from sync.source_db import set_source_engine

        eng = create_engine("sqlite://")
        set_source_engine(eng)

    def test_public_reset_source_engine(self):
        """line 64-65: reset_source_engine() public function."""
        from sync.source_db import reset_source_engine

        reset_source_engine()
