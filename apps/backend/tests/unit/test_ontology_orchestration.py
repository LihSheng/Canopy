"""Unit tests for ontology orchestration service and repository edge cases."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.business_rule


class TestOntologyOrchestrator:
    """Cover OntologyOrchestrator initialization and map_all flow.

    lines 29-30: __init__ stores db and creates OntologyRepository.
    lines 42-66: map_all runs all mappers and persists results.
    lines 73-88: _persist dispatches by entity_type.
    """

    def test_init_creates_repo(self):
        from ontology.orchestration.service import OntologyOrchestrator

        orch = OntologyOrchestrator(MagicMock())
        assert orch._db is not None
        assert orch._repo is not None

    def test_map_all_runs_all_mappers(self):
        with (
            patch("ontology.orchestration.service.DepartmentMapper") as mock_dept_mapper,
            patch("ontology.orchestration.service.CostCenterMapper") as mock_cc_mapper,
            patch("ontology.orchestration.service.BudgetCodeMapper") as mock_bc_mapper,
            patch("ontology.orchestration.service.EmployeeMapper") as mock_emp_mapper,
            patch("ontology.orchestration.service.ClaimMapper") as mock_claim_mapper,
            patch("ontology.orchestration.service.PayrollMapper") as mock_pay_mapper,
        ):
            # Each mapper returns a MagicMock with entity_type and mapped/unresolved
            for m in [
                mock_dept_mapper,
                mock_cc_mapper,
                mock_bc_mapper,
                mock_emp_mapper,
                mock_claim_mapper,
                mock_pay_mapper,
            ]:
                instance = MagicMock()
                result = MagicMock()
                result.entity_type = "unknown"
                result.mapped = []
                result.unresolved = []
                instance.map.return_value = result
                m.return_value = instance

            mock_db = MagicMock()
            from ontology.orchestration.service import OntologyOrchestrator

            orch = OntologyOrchestrator(mock_db)
            orch._persist = MagicMock()

            results = orch.map_all(
                snapshot_id="snap-1",
                departments=[],
                employees=[],
                cost_centers=[],
                budget_codes=[],
                claims=[],
                payroll=[],
            )

            assert len(results) == 6
            assert mock_db.commit.called

    def test_persist_dispatches_by_entity_type(self):
        """lines 73-88: _persist routes to correct save method."""
        from ontology.domain import (
            BudgetCode,
            CostCenter,
            Department,
            Employee,
            ExpenseClaim,
            MappingResult,
            PayrollExpense,
        )
        from ontology.orchestration.service import OntologyOrchestrator

        mock_db = MagicMock()
        orch = OntologyOrchestrator(mock_db)
        orch._repo = MagicMock()

        dept = Department(id="d1", snapshot_id="s1", source_department_key="sk1", source_lineage="{}", name="Eng")
        emp = MagicMock(spec=Employee)
        cc = MagicMock(spec=CostCenter)
        bc = MagicMock(spec=BudgetCode)
        claim = MagicMock(spec=ExpenseClaim)
        payroll = MagicMock(spec=PayrollExpense)

        results = [
            MappingResult(entity_type="departments", snapshot_id="s1", mapped=[dept], unresolved=[]),
            MappingResult(entity_type="employees", snapshot_id="s1", mapped=[emp], unresolved=[]),
            MappingResult(entity_type="cost_centers", snapshot_id="s1", mapped=[cc], unresolved=[]),
            MappingResult(entity_type="budget_codes", snapshot_id="s1", mapped=[bc], unresolved=[]),
            MappingResult(entity_type="expense_claims", snapshot_id="s1", mapped=[claim], unresolved=[]),
            MappingResult(entity_type="payroll_expenses", snapshot_id="s1", mapped=[payroll], unresolved=[]),
        ]

        orch._persist(results, "s1")

        assert orch._repo.save_departments.called
        assert orch._repo.save_employees.called
        assert orch._repo.save_cost_centers.called
        assert orch._repo.save_budget_codes.called
        assert orch._repo.save_expense_claims.called
        assert orch._repo.save_payroll_expenses.called

    def test_persist_with_unresolved_issues(self):
        """line 87-88: unresolved records are saved."""
        from ontology.domain import MappingResult, UnresolvedRecord
        from ontology.orchestration.service import OntologyOrchestrator

        mock_db = MagicMock()
        orch = OntologyOrchestrator(mock_db)
        orch._repo = MagicMock()

        unresolved = [UnresolvedRecord(source_key="e1", entity_type="employees", reason="missing dept")]
        results = [
            MappingResult(entity_type="departments", snapshot_id="s1", mapped=[], unresolved=unresolved),
        ]

        orch._persist(results, "s1")
        assert orch._repo.save_unresolved_issues.called


class TestAttributionResolverEdgeCases:
    """Cover AttributionResolver edge cases (lines 22-25, 37)."""

    def test_cost_center_with_mapped_code_returns_none(self):
        """lines 22-25: cost center exists and has a code -> returns None."""
        from ontology.domain import CostCenter, MappingContext
        from ontology.mappers.attribution import AttributionResolver

        cc = CostCenter(
            id="cc1",
            snapshot_id="s1",
            source_cost_center_key="CC01",
            source_lineage="{}",
            code="CC01",
            name="R&D",
        )
        context = MappingContext(snapshot_id="s1", cost_centers={"CC01": cc})

        resolver = AttributionResolver()
        result = resolver.resolve_department(
            context,
            direct_department_key=None,
            employee_source_key=None,
            cost_center_source_key="CC01",
        )
        assert result is None

    def test_cost_center_not_in_context_returns_none(self):
        """cost_center_source_key not in context -> returns None."""
        from ontology.domain import MappingContext
        from ontology.mappers.attribution import AttributionResolver

        context = MappingContext(snapshot_id="s1")
        resolver = AttributionResolver()
        result = resolver.resolve_department(
            context,
            direct_department_key=None,
            employee_source_key=None,
            cost_center_source_key="CC999",
        )
        assert result is None

    def test_resolve_cost_center_unknown_employee_returns_none(self):
        """line 37: employee not in context -> returns None."""
        from ontology.domain import MappingContext
        from ontology.mappers.attribution import AttributionResolver

        context = MappingContext(snapshot_id="s1")
        resolver = AttributionResolver()
        result = resolver.resolve_cost_center(context, employee_source_key="E999")
        assert result is None


class TestEmployeeMapperCostCenter:
    """Cover EmployeeMapper cost_center_id assignment (departments.py line 94)."""

    def test_employee_with_known_cost_center(self):
        from ontology.domain import CostCenter, Department, MappingContext
        from ontology.mappers.departments import EmployeeMapper
        from sync.domain import SourceEmployee

        dept = Department(id="d1", snapshot_id="s1", source_department_key="D001", source_lineage="{}", name="Eng")
        cc = CostCenter(
            id="cc1", snapshot_id="s1", source_cost_center_key="CC01", source_lineage="{}", code="CC01", name="R&D"
        )
        context = MappingContext(
            snapshot_id="s1",
            departments={"D001": dept},
            cost_centers={"CC01": cc},
        )
        mapper = EmployeeMapper()
        source = [
            SourceEmployee(source_key="E001", full_name="Alice", department_key="D001", cost_center_key="CC01"),
        ]

        result = mapper.map(source, context)
        assert len(result.mapped) == 1
        assert result.mapped[0].cost_center_id == "cc1"

    def test_employee_with_unknown_cost_center(self):
        """line 93-94: cost_center_key not in context -> cost_center_id = None."""
        from ontology.domain import Department, MappingContext
        from ontology.mappers.departments import EmployeeMapper
        from sync.domain import SourceEmployee

        dept = Department(id="d1", snapshot_id="s1", source_department_key="D001", source_lineage="{}", name="Eng")
        context = MappingContext(
            snapshot_id="s1",
            departments={"D001": dept},
        )
        mapper = EmployeeMapper()
        source = [
            SourceEmployee(source_key="E001", full_name="Alice", department_key="D001", cost_center_key="CC999"),
        ]

        result = mapper.map(source, context)
        assert len(result.mapped) == 1
        assert result.mapped[0].cost_center_id is None
