import pytest

import uuid
from datetime import datetime

from ontology.domain import MappingContext
from ontology.mappers import (
    BudgetCodeMapper,
    CostCenterMapper,
    DepartmentMapper,
    EmployeeMapper,
)
from sync.domain import (
    SourceBudgetCode,
    SourceCostCenter,
    SourceDepartment,
    SourceEmployee,
)

pytestmark = pytest.mark.business_rule


class TestDepartmentMapper:
    def test_maps_single_department(self):
        mapper = DepartmentMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceDepartment(
                source_key="D001", name="Engineering", status="active"
            )
        ]

        result = mapper.map(source, context)

        assert result.entity_type == "departments"
        assert result.snapshot_id == "snap-001"
        assert len(result.mapped) == 1
        assert len(result.unresolved) == 0

        dept = result.mapped[0]
        assert dept.source_department_key == "D001"
        assert dept.name == "Engineering"
        assert dept.status == "active"
        assert dept.snapshot_id == "snap-001"
        assert dept.id != ""
        assert "source_key" in dept.source_lineage
        assert dept.parent_department_id is None

    def test_registers_in_context(self):
        mapper = DepartmentMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceDepartment(source_key="D001", name="Engineering"),
            SourceDepartment(source_key="D002", name="Marketing"),
        ]

        mapper.map(source, context)

        assert "D001" in context.departments
        assert "D002" in context.departments
        assert context.departments["D001"].name == "Engineering"
        assert context.departments["D002"].name == "Marketing"

    def test_empty_source_returns_empty_result(self):
        mapper = DepartmentMapper()
        context = MappingContext(snapshot_id="snap-001")

        result = mapper.map([], context)

        assert result.mapped == []
        assert result.unresolved == []

    def test_entity_type(self):
        assert DepartmentMapper().entity_type == "departments"


class TestEmployeeMapper:
    def test_maps_employee_with_resolved_department(self):
        mapper = EmployeeMapper()
        from ontology.domain import Department

        dept = Department(
            id="dept-id-1",
            snapshot_id="snap-001",
            source_department_key="D001",
            source_lineage="{}",
            name="Engineering",
        )
        context = MappingContext(
            snapshot_id="snap-001", departments={"D001": dept}
        )
        source = [
            SourceEmployee(
                source_key="E001",
                full_name="Alice Tan",
                department_key="D001",
                cost_center_key="CC01",
            )
        ]

        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        emp = result.mapped[0]
        assert emp.source_employee_key == "E001"
        assert emp.full_name == "Alice Tan"
        assert emp.department_id == "dept-id-1"
        assert emp.employee_code == "E001"
        assert emp.employment_status == "active"

    def test_employee_with_missing_department_is_unresolved(self):
        mapper = EmployeeMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceEmployee(
                source_key="E001",
                full_name="Bob Lim",
                department_key="D999",
            )
        ]

        result = mapper.map(source, context)

        assert len(result.mapped) == 0
        assert len(result.unresolved) == 1
        assert result.unresolved[0].entity_type == "employees"
        assert result.unresolved[0].source_key == "E001"
        assert "D999" in result.unresolved[0].reason

    def test_employee_with_null_cost_center(self):
        mapper = EmployeeMapper()
        from ontology.domain import Department

        dept = Department(
            id="dept-id-2",
            snapshot_id="snap-001",
            source_department_key="D002",
            source_lineage="{}",
            name="Marketing",
        )
        context = MappingContext(
            snapshot_id="snap-001", departments={"D002": dept}
        )
        source = [
            SourceEmployee(
                source_key="E002",
                full_name="Charlie",
                department_key="D002",
                cost_center_key=None,
            )
        ]

        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        assert result.mapped[0].cost_center_id is None


class TestCostCenterMapper:
    def test_maps_single_cost_center(self):
        mapper = CostCenterMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceCostCenter(
                source_key="CC001", name="R&D", department_key="D001"
            )
        ]

        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        cc = result.mapped[0]
        assert cc.source_cost_center_key == "CC001"
        assert cc.name == "R&D"
        assert cc.code == "CC001"
        assert cc.snapshot_id == "snap-001"

    def test_registers_in_context(self):
        mapper = CostCenterMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceCostCenter(source_key="CC001", name="R&D"),
            SourceCostCenter(source_key="CC002", name="Admin"),
        ]

        mapper.map(source, context)

        assert "CC001" in context.cost_centers
        assert "CC002" in context.cost_centers


class TestBudgetCodeMapper:
    def test_maps_single_budget_code(self):
        mapper = BudgetCodeMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceBudgetCode(
                source_key="B001", name="Opex-IT", department_key="D001"
            )
        ]

        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        bc = result.mapped[0]
        assert bc.source_budget_code_key == "B001"
        assert bc.name == "Opex-IT"
        assert bc.code == "B001"

    def test_registers_in_context(self):
        mapper = BudgetCodeMapper()
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceBudgetCode(source_key="B001", name="Opex-IT"),
            SourceBudgetCode(source_key="B002", name="Capex"),
        ]

        mapper.map(source, context)

        assert "B001" in context.budget_codes
        assert "B002" in context.budget_codes
