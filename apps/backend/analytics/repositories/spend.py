from collections import defaultdict
from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy.orm import Session

from analytics.domain import (
    ClaimDetailSummary,
    DashboardSummaryCache,
    EmployeeContributionSummary,
    MonthlyClaimTypeSpend,
    MonthlyDepartmentSpend,
    MonthlyEmployeeSpend,
)
from analytics.schema import (
    DashboardSummaryCacheModel,
    MonthlyClaimTypeSpendModel,
    MonthlyDepartmentSpendModel,
    MonthlyEmployeeSpendModel,
)
from common.clock import utcnow
from ontology.schema import (
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
)


class SpendRepository:
    """Persistence and queries for department, employee, and claim-type spend data."""

    def __init__(self, db: Session):
        self._db = db

    # ---- persistence ----

    def save_department_spends(
        self, spends: list[MonthlyDepartmentSpend]
    ) -> list[MonthlyDepartmentSpendModel]:
        models = [
            MonthlyDepartmentSpendModel(
                id=s.id,
                snapshot_id=s.snapshot_id,
                department_id=s.department_id,
                month=s.month,
                payroll_total=s.payroll_total,
                claims_total=s.claims_total,
                total=s.total,
                claim_count=s.claim_count,
            )
            for s in spends
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_employee_spends(
        self, spends: list[MonthlyEmployeeSpend]
    ) -> list[MonthlyEmployeeSpendModel]:
        models = [
            MonthlyEmployeeSpendModel(
                id=s.id,
                snapshot_id=s.snapshot_id,
                employee_id=s.employee_id,
                department_id=s.department_id,
                month=s.month,
                payroll_total=s.payroll_total,
                claims_total=s.claims_total,
                total=s.total,
            )
            for s in spends
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def save_claim_type_spends(
        self, spends: list[MonthlyClaimTypeSpend]
    ) -> list[MonthlyClaimTypeSpendModel]:
        models = [
            MonthlyClaimTypeSpendModel(
                id=s.id,
                snapshot_id=s.snapshot_id,
                department_id=s.department_id,
                claim_type=s.claim_type,
                month=s.month,
                amount=s.amount,
                claim_count=s.claim_count,
            )
            for s in spends
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def clear_spends_for_snapshot(self, snapshot_id: str) -> None:
        self._db.query(MonthlyDepartmentSpendModel).filter(
            MonthlyDepartmentSpendModel.snapshot_id == snapshot_id
        ).delete()
        self._db.query(MonthlyEmployeeSpendModel).filter(
            MonthlyEmployeeSpendModel.snapshot_id == snapshot_id
        ).delete()
        self._db.query(MonthlyClaimTypeSpendModel).filter(
            MonthlyClaimTypeSpendModel.snapshot_id == snapshot_id
        ).delete()
        self._db.commit()

    # ---- monthly department spends ----

    def get_monthly_spends_for_month(
        self, month: str, snapshot_id: str | None = None
    ) -> list[MonthlyDepartmentSpend]:
        q = self._db.query(MonthlyDepartmentSpendModel).filter(
            MonthlyDepartmentSpendModel.month == month
        )
        if snapshot_id:
            q = q.filter(MonthlyDepartmentSpendModel.snapshot_id == snapshot_id)
        return [_model_to_domain(m) for m in q.order_by(MonthlyDepartmentSpendModel.total.desc()).all()]

    def get_monthly_spends_for_department(
        self, department_id: str, snapshot_id: str | None = None
    ) -> list[MonthlyDepartmentSpend]:
        q = self._db.query(MonthlyDepartmentSpendModel).filter(
            MonthlyDepartmentSpendModel.department_id == department_id
        )
        if snapshot_id:
            q = q.filter(MonthlyDepartmentSpendModel.snapshot_id == snapshot_id)
        return [
            _model_to_domain(m)
            for m in q.order_by(MonthlyDepartmentSpendModel.month.asc()).all()
        ]

    def get_all_monthly_spends(
        self, snapshot_id: str | None = None
    ) -> list[MonthlyDepartmentSpend]:
        q = self._db.query(MonthlyDepartmentSpendModel)
        if snapshot_id:
            q = q.filter(MonthlyDepartmentSpendModel.snapshot_id == snapshot_id)
        return [
            _model_to_domain(m)
            for m in q.order_by(MonthlyDepartmentSpendModel.month.asc()).all()
        ]

    def get_distinct_months(self, snapshot_id: str | None = None) -> list[str]:
        q = self._db.query(MonthlyDepartmentSpendModel.month).distinct()
        if snapshot_id:
            q = q.filter(MonthlyDepartmentSpendModel.snapshot_id == snapshot_id)
        return sorted(
            [row[0] for row in q.all()],
            reverse=True,
        )

    def get_snapshot_id_from_aggregates(self) -> str | None:
        row = (
            self._db.query(MonthlyDepartmentSpendModel.snapshot_id)
            .order_by(MonthlyDepartmentSpendModel.month.desc())
            .first()
        )
        return row[0] if row else None

    # ---- monthly employee spends ----

    def get_employee_spends_for_department(
        self, department_id: str, month: str | None = None, snapshot_id: str | None = None
    ) -> list[MonthlyEmployeeSpend]:
        q = self._db.query(MonthlyEmployeeSpendModel).filter(
            MonthlyEmployeeSpendModel.department_id == department_id
        )
        if month:
            q = q.filter(MonthlyEmployeeSpendModel.month == month)
        if snapshot_id:
            q = q.filter(MonthlyEmployeeSpendModel.snapshot_id == snapshot_id)
        return [
            MonthlyEmployeeSpend(
                id=m.id,
                snapshot_id=m.snapshot_id,
                employee_id=m.employee_id,
                department_id=m.department_id,
                month=m.month,
                payroll_total=m.payroll_total,
                claims_total=m.claims_total,
                total=m.total,
            )
            for m in q.order_by(MonthlyEmployeeSpendModel.total.desc()).all()
        ]

    # ---- claim type spends ----

    def get_claim_type_spends(
        self,
        department_id: str | None = None,
        month: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[MonthlyClaimTypeSpend]:
        q = self._db.query(MonthlyClaimTypeSpendModel)
        if department_id is not None:
            q = q.filter(MonthlyClaimTypeSpendModel.department_id == department_id)
        if month:
            q = q.filter(MonthlyClaimTypeSpendModel.month == month)
        if snapshot_id:
            q = q.filter(MonthlyClaimTypeSpendModel.snapshot_id == snapshot_id)
        return [
            MonthlyClaimTypeSpend(
                id=m.id,
                snapshot_id=m.snapshot_id,
                department_id=m.department_id,
                claim_type=m.claim_type,
                month=m.month,
                amount=m.amount,
                claim_count=m.claim_count,
            )
            for m in q.order_by(MonthlyClaimTypeSpendModel.amount.desc()).all()
        ]

    # ---- cross-entity queries ----

    def get_employee_contributions(
        self,
        department_id: str,
        month: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[EmployeeContributionSummary]:
        q = self._db.query(
            MonthlyEmployeeSpendModel, EmployeeModel.full_name, DepartmentModel.name
        ).join(
            EmployeeModel,
            MonthlyEmployeeSpendModel.employee_id == EmployeeModel.id,
        ).join(
            DepartmentModel,
            MonthlyEmployeeSpendModel.department_id == DepartmentModel.id,
        ).filter(
            MonthlyEmployeeSpendModel.department_id == department_id
        )

        if month:
            q = q.filter(MonthlyEmployeeSpendModel.month == month)
        if snapshot_id:
            q = q.filter(MonthlyEmployeeSpendModel.snapshot_id == snapshot_id)
            q = q.filter(EmployeeModel.snapshot_id == snapshot_id)
            q = q.filter(DepartmentModel.snapshot_id == snapshot_id)

        return [
            EmployeeContributionSummary(
                employee_id=row.MonthlyEmployeeSpendModel.employee_id,
                employee_name=row.full_name or row.MonthlyEmployeeSpendModel.employee_id,
                department_id=row.MonthlyEmployeeSpendModel.department_id,
                department_name=row.name or "",
                month=row.MonthlyEmployeeSpendModel.month,
                payroll=row.MonthlyEmployeeSpendModel.payroll_total,
                claims=row.MonthlyEmployeeSpendModel.claims_total,
                total=row.MonthlyEmployeeSpendModel.total,
            )
            for row in q.order_by(MonthlyEmployeeSpendModel.total.desc()).all()
        ]

    def get_claim_details(
        self,
        department_id: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[ClaimDetailSummary]:
        q = self._db.query(
            ExpenseClaimModel, EmployeeModel.full_name, DepartmentModel.name
        ).join(
            EmployeeModel,
            ExpenseClaimModel.employee_id == EmployeeModel.id,
        ).join(
            DepartmentModel,
            ExpenseClaimModel.department_id == DepartmentModel.id,
        )

        if department_id:
            q = q.filter(ExpenseClaimModel.department_id == department_id)
        if snapshot_id:
            q = q.filter(ExpenseClaimModel.snapshot_id == snapshot_id)
            q = q.filter(EmployeeModel.snapshot_id == snapshot_id)
            q = q.filter(DepartmentModel.snapshot_id == snapshot_id)

        return [
            ClaimDetailSummary(
                claim_id=row.ExpenseClaimModel.id,
                employee_name=row.full_name or row.ExpenseClaimModel.employee_id,
                department_id=row.ExpenseClaimModel.department_id or "",
                department_name=row.name or "",
                claim_type=row.ExpenseClaimModel.claim_type,
                amount=row.ExpenseClaimModel.amount,
                claim_date=row.ExpenseClaimModel.claim_date,
            )
            for row in q.order_by(ExpenseClaimModel.claim_date.desc()).all()
        ]

    def get_department_map(self, snapshot_id: str | None = None) -> dict[str, str]:
        q = self._db.query(DepartmentModel)
        if snapshot_id:
            q = q.filter(DepartmentModel.snapshot_id == snapshot_id)
        models = q.all()
        return {m.id: m.name for m in models}

    def get_department_count_for_snapshot(self, snapshot_id: str) -> int:
        return (
            self._db.query(DepartmentModel)
            .filter(DepartmentModel.snapshot_id == snapshot_id)
            .count()
        )


def _model_to_domain(m: MonthlyDepartmentSpendModel) -> MonthlyDepartmentSpend:
    return MonthlyDepartmentSpend(
        id=m.id,
        snapshot_id=m.snapshot_id,
        department_id=m.department_id,
        month=m.month,
        payroll_total=m.payroll_total,
        claims_total=m.claims_total,
        total=m.total,
        claim_count=m.claim_count,
    )
