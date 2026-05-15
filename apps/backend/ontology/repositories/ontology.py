import json
from dataclasses import asdict
from typing import Any, Sequence

from sqlalchemy.orm import Session

from ontology.domain import (
    BudgetCode,
    CostCenter,
    Department,
    Employee,
    ExpenseClaim,
    PayrollExpense,
    UnresolvedRecord,
)
from ontology.schema import (
    BudgetCodeModel,
    CostCenterModel,
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
    PayrollExpenseModel,
    UnresolvedMappingIssueModel,
)


class OntologyRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_departments(
        self, departments: Sequence[Department]
    ) -> list[DepartmentModel]:
        models = [
            DepartmentModel(
                id=d.id,
                snapshot_id=d.snapshot_id,
                source_department_key=d.source_department_key,
                source_lineage=d.source_lineage,
                name=d.name,
                parent_department_id=d.parent_department_id,
                status=d.status,
            )
            for d in departments
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_employees(
        self, employees: Sequence[Employee]
    ) -> list[EmployeeModel]:
        models = [
            EmployeeModel(
                id=e.id,
                snapshot_id=e.snapshot_id,
                source_employee_key=e.source_employee_key,
                source_lineage=e.source_lineage,
                department_id=e.department_id,
                cost_center_id=e.cost_center_id,
                employee_code=e.employee_code,
                full_name=e.full_name,
                employment_status=e.employment_status,
            )
            for e in employees
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_cost_centers(
        self, cost_centers: Sequence[CostCenter]
    ) -> list[CostCenterModel]:
        models = [
            CostCenterModel(
                id=c.id,
                snapshot_id=c.snapshot_id,
                source_cost_center_key=c.source_cost_center_key,
                source_lineage=c.source_lineage,
                code=c.code,
                name=c.name,
            )
            for c in cost_centers
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_budget_codes(
        self, budget_codes: Sequence[BudgetCode]
    ) -> list[BudgetCodeModel]:
        models = [
            BudgetCodeModel(
                id=b.id,
                snapshot_id=b.snapshot_id,
                source_budget_code_key=b.source_budget_code_key,
                source_lineage=b.source_lineage,
                code=b.code,
                name=b.name,
                category=b.category,
            )
            for b in budget_codes
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_expense_claims(
        self, claims: Sequence[ExpenseClaim]
    ) -> list[ExpenseClaimModel]:
        models = [
            ExpenseClaimModel(
                id=c.id,
                snapshot_id=c.snapshot_id,
                source_claim_key=c.source_claim_key,
                source_lineage=c.source_lineage,
                employee_id=c.employee_id,
                department_id=c.department_id,
                cost_center_id=c.cost_center_id,
                budget_code_id=c.budget_code_id,
                claim_type=c.claim_type,
                claim_date=c.claim_date,
                amount=c.amount,
                currency=c.currency,
                is_resolved=c.is_resolved,
            )
            for c in claims
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_payroll_expenses(
        self, payroll: Sequence[PayrollExpense]
    ) -> list[PayrollExpenseModel]:
        models = [
            PayrollExpenseModel(
                id=p.id,
                snapshot_id=p.snapshot_id,
                source_payroll_key=p.source_payroll_key,
                source_lineage=p.source_lineage,
                employee_id=p.employee_id,
                department_id=p.department_id,
                cost_center_id=p.cost_center_id,
                budget_code_id=p.budget_code_id,
                payroll_month=p.payroll_month,
                amount=p.amount,
                currency=p.currency,
                pay_component=p.pay_component,
                is_resolved=p.is_resolved,
            )
            for p in payroll
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_unresolved_issues(
        self,
        snapshot_id: str,
        issues: Sequence[UnresolvedRecord],
    ) -> list[UnresolvedMappingIssueModel]:
        models = [
            UnresolvedMappingIssueModel(
                snapshot_id=snapshot_id,
                entity_type=i.entity_type,
                source_key=i.source_key,
                reason=i.reason,
                source_data=json.dumps(i.source_data, default=str),
            )
            for i in issues
        ]
        if models:
            self._db.add_all(models)
            self._db.commit()
        return models

    def department_count_for_snapshot(self, snapshot_id: str) -> int:
        return (
            self._db.query(DepartmentModel)
            .filter(DepartmentModel.snapshot_id == snapshot_id)
            .count()
        )

    def employee_count_for_snapshot(self, snapshot_id: str) -> int:
        return (
            self._db.query(EmployeeModel)
            .filter(EmployeeModel.snapshot_id == snapshot_id)
            .count()
        )

    def expense_claim_count_for_snapshot(self, snapshot_id: str) -> int:
        return (
            self._db.query(ExpenseClaimModel)
            .filter(ExpenseClaimModel.snapshot_id == snapshot_id)
            .count()
        )

    def payroll_expense_count_for_snapshot(self, snapshot_id: str) -> int:
        return (
            self._db.query(PayrollExpenseModel)
            .filter(PayrollExpenseModel.snapshot_id == snapshot_id)
            .count()
        )

    def unresolved_issue_count_for_snapshot(self, snapshot_id: str) -> int:
        return (
            self._db.query(UnresolvedMappingIssueModel)
            .filter(UnresolvedMappingIssueModel.snapshot_id == snapshot_id)
            .count()
        )
