from typing import Any

from sqlalchemy.orm import Session

from ontology.domain import MappingContext, MappingResult
from ontology.mappers import (
    BudgetCodeMapper,
    ClaimMapper,
    CostCenterMapper,
    DepartmentMapper,
    EmployeeMapper,
    PayrollMapper,
)
from ontology.repositories.ontology import OntologyRepository
from sync.domain import (
    SourceBudgetCode,
    SourceClaim,
    SourceCostCenter,
    SourceDepartment,
    SourceEmployee,
    SourcePayroll,
)


class OntologyOrchestrator:
    def __init__(self, db: Session):
        self._db = db
        self._repo = OntologyRepository(db)

    def map_all(
        self,
        snapshot_id: str,
        departments: list[SourceDepartment],
        employees: list[SourceEmployee],
        cost_centers: list[SourceCostCenter],
        budget_codes: list[SourceBudgetCode],
        claims: list[SourceClaim],
        payroll: list[SourcePayroll],
    ) -> list[MappingResult[Any]]:
        context = MappingContext(snapshot_id=snapshot_id)
        results: list[MappingResult[Any]] = []

        dep_result = DepartmentMapper().map(departments, context)
        results.append(dep_result)

        cc_result = CostCenterMapper().map(cost_centers, context)
        results.append(cc_result)

        bc_result = BudgetCodeMapper().map(budget_codes, context)
        results.append(bc_result)

        emp_result = EmployeeMapper().map(employees, context)
        results.append(emp_result)

        claim_result = ClaimMapper().map(claims, context)
        results.append(claim_result)

        payroll_result = PayrollMapper().map(payroll, context)
        results.append(payroll_result)

        self._persist(results, snapshot_id)
        self._db.commit()

        return results

    def _persist(
        self,
        results: list[MappingResult[Any]],
        snapshot_id: str,
    ) -> None:
        for r in results:
            if r.entity_type == "departments":
                self._repo.save_departments(r.mapped)
            elif r.entity_type == "employees":
                self._repo.save_employees(r.mapped)
            elif r.entity_type == "cost_centers":
                self._repo.save_cost_centers(r.mapped)
            elif r.entity_type == "budget_codes":
                self._repo.save_budget_codes(r.mapped)
            elif r.entity_type == "expense_claims":
                self._repo.save_expense_claims(r.mapped)
            elif r.entity_type == "payroll_expenses":
                self._repo.save_payroll_expenses(r.mapped)

            if r.unresolved:
                self._repo.save_unresolved_issues(snapshot_id, r.unresolved)
