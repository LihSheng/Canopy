import json
import uuid
from dataclasses import asdict

from ontology.domain import (
    BudgetCode,
    CostCenter,
    Department,
    Employee,
    ExpenseClaim,
    MappingContext,
    MappingResult,
    OntologyMapper,
    PayrollExpense,
    UnresolvedRecord,
)
from sync.domain import (
    SourceBudgetCode,
    SourceClaim,
    SourceCostCenter,
    SourceDepartment,
    SourceEmployee,
    SourcePayroll,
)


def _make_lineage(source_entity: object) -> str:
    return json.dumps(asdict(source_entity), default=str)


class DepartmentMapper(OntologyMapper[SourceDepartment, Department]):
    entity_type = "departments"

    def map(
        self,
        source_rows: list[SourceDepartment],
        context: MappingContext,
    ) -> MappingResult[Department]:
        mapped: list[Department] = []
        unresolved: list[UnresolvedRecord] = []

        for src in source_rows:
            lineage = _make_lineage(src)
            dept = Department(
                id=str(uuid.uuid4()),
                snapshot_id=context.snapshot_id,
                source_department_key=src.source_key,
                source_lineage=lineage,
                name=src.name,
                parent_department_id=None,
                status=src.status,
            )
            mapped.append(dept)
            context.departments[src.source_key] = dept

        return MappingResult(
            entity_type=self.entity_type,
            snapshot_id=context.snapshot_id,
            mapped=mapped,
            unresolved=unresolved,
        )


class EmployeeMapper(OntologyMapper[SourceEmployee, Employee]):
    entity_type = "employees"

    def map(
        self,
        source_rows: list[SourceEmployee],
        context: MappingContext,
    ) -> MappingResult[Employee]:
        mapped: list[Employee] = []
        unresolved: list[UnresolvedRecord] = []

        for src in source_rows:
            lineage = _make_lineage(src)

            department_id = ""
            if src.department_key in context.departments:
                department_id = context.departments[src.department_key].id
            else:
                unresolved.append(
                    UnresolvedRecord(
                        source_key=src.source_key,
                        entity_type=self.entity_type,
                        reason=f"department {src.department_key} not found",
                        source_data=asdict(src),
                    )
                )
                continue

            cost_center_id = None
            if src.cost_center_key and src.cost_center_key in context.cost_centers:
                cost_center_id = context.cost_centers[src.cost_center_key].id

            employee = Employee(
                id=str(uuid.uuid4()),
                snapshot_id=context.snapshot_id,
                source_employee_key=src.source_key,
                source_lineage=lineage,
                department_id=department_id,
                cost_center_id=cost_center_id,
                employee_code=src.source_key,
                full_name=src.full_name,
                employment_status="active",
            )
            mapped.append(employee)
            context.employees[src.source_key] = employee

        return MappingResult(
            entity_type=self.entity_type,
            snapshot_id=context.snapshot_id,
            mapped=mapped,
            unresolved=unresolved,
        )


class CostCenterMapper(OntologyMapper[SourceCostCenter, CostCenter]):
    entity_type = "cost_centers"

    def map(
        self,
        source_rows: list[SourceCostCenter],
        context: MappingContext,
    ) -> MappingResult[CostCenter]:
        mapped: list[CostCenter] = []
        unresolved: list[UnresolvedRecord] = []

        for src in source_rows:
            lineage = _make_lineage(src)
            cc = CostCenter(
                id=str(uuid.uuid4()),
                snapshot_id=context.snapshot_id,
                source_cost_center_key=src.source_key,
                source_lineage=lineage,
                code=src.source_key,
                name=src.name,
            )
            mapped.append(cc)
            context.cost_centers[src.source_key] = cc

        return MappingResult(
            entity_type=self.entity_type,
            snapshot_id=context.snapshot_id,
            mapped=mapped,
            unresolved=unresolved,
        )


class BudgetCodeMapper(OntologyMapper[SourceBudgetCode, BudgetCode]):
    entity_type = "budget_codes"

    def map(
        self,
        source_rows: list[SourceBudgetCode],
        context: MappingContext,
    ) -> MappingResult[BudgetCode]:
        mapped: list[BudgetCode] = []
        unresolved: list[UnresolvedRecord] = []

        for src in source_rows:
            lineage = _make_lineage(src)
            bc = BudgetCode(
                id=str(uuid.uuid4()),
                snapshot_id=context.snapshot_id,
                source_budget_code_key=src.source_key,
                source_lineage=lineage,
                code=src.source_key,
                name=src.name,
                category="",
            )
            mapped.append(bc)
            context.budget_codes[src.source_key] = bc

        return MappingResult(
            entity_type=self.entity_type,
            snapshot_id=context.snapshot_id,
            mapped=mapped,
            unresolved=unresolved,
        )
