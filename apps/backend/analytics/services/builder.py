from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from analytics.aggregators.claims import (
    aggregate_claims_by_department,
    aggregate_claims_by_employee,
    aggregate_claims_by_type,
)
from analytics.aggregators.deltas import (
    attach_mom_deltas_to_rankings,
    calculate_mom_deltas,
    rank_departments,
)
from analytics.aggregators.merge import merge_department_spend, merge_employee_spend
from analytics.aggregators.payroll import (
    aggregate_payroll_by_department,
    aggregate_payroll_by_employee,
)
from analytics.domain import DashboardSummaryCache, DepartmentRanking, MonthlyDepartmentSpend
from analytics.repositories.spend import SpendRepository
from analytics.repositories.dashboard_cache import DashboardCacheRepository
from common.clock import utcnow
from ontology.schema import ExpenseClaimModel, PayrollExpenseModel


def run_aggregation_pipeline(
    db: Session,
    snapshot_id: str,
    current_month: str,
    previous_month: str,
    anomaly_count: int = 0,
) -> DashboardSummaryCache:
    spend_repo = SpendRepository(db)
    cache_repo = DashboardCacheRepository(db)
    spend_repo.clear_spends_for_snapshot(snapshot_id)
    cache_repo.clear_snapshot(snapshot_id)

    payroll_rows = _read_payroll_rows(db, snapshot_id)
    claim_rows = _read_claim_rows(db, snapshot_id)

    payroll_dept_spends = aggregate_payroll_by_department(snapshot_id, payroll_rows)
    claim_dept_spends = aggregate_claims_by_department(snapshot_id, claim_rows)
    merged_dept_spends = merge_department_spend(snapshot_id, payroll_dept_spends, claim_dept_spends)

    spend_repo.save_department_spends(merged_dept_spends)

    payroll_emp = aggregate_payroll_by_employee(snapshot_id, payroll_rows)
    claim_emp = aggregate_claims_by_employee(snapshot_id, claim_rows)
    merged_emp_spends = merge_employee_spend(snapshot_id, payroll_emp, claim_emp)
    spend_repo.save_employee_spends(merged_emp_spends)

    claim_type_spends = aggregate_claims_by_type(snapshot_id, claim_rows)
    spend_repo.save_claim_type_spends(claim_type_spends)

    summary = _build_summary(
        spend_repo=spend_repo,
        snapshot_id=snapshot_id,
        merged_spends=merged_dept_spends,
        current_month=current_month,
        anomaly_count=anomaly_count,
    )
    cache_repo.save_summary_cache(summary)

    return summary


def _build_summary(
    spend_repo: SpendRepository,
    snapshot_id: str,
    merged_spends: list[MonthlyDepartmentSpend],
    current_month: str,
    anomaly_count: int,
) -> DashboardSummaryCache:
    dept_count = spend_repo.get_department_count_for_snapshot(snapshot_id)

    total_payroll = sum(s.payroll_total for s in merged_spends if s.month == current_month)
    total_claims = sum(s.claims_total for s in merged_spends if s.month == current_month)

    month_parts = current_month.split("-")
    year = int(month_parts[0]) if len(month_parts) == 2 else datetime.now().year
    month = int(month_parts[1]) if len(month_parts) == 2 else datetime.now().month

    return DashboardSummaryCache(
        snapshot_id=snapshot_id,
        year=year,
        month=month,
        total_payroll=total_payroll,
        total_claims=total_claims,
        department_count=dept_count,
        anomaly_count=anomaly_count,
        created_at=utcnow(),
    )


def _read_payroll_rows(db: Session, snapshot_id: str) -> list[dict]:
    models = (
        db.query(PayrollExpenseModel)
        .filter(
            PayrollExpenseModel.snapshot_id == snapshot_id,
            PayrollExpenseModel.is_resolved == True,
        )
        .all()
    )
    return [
        {
            "employee_id": m.employee_id,
            "department_id": m.department_id,
            "payroll_month": m.payroll_month,
            "amount": m.amount,
        }
        for m in models
    ]


def _read_claim_rows(db: Session, snapshot_id: str) -> list[dict]:
    models = (
        db.query(ExpenseClaimModel)
        .filter(
            ExpenseClaimModel.snapshot_id == snapshot_id,
            ExpenseClaimModel.is_resolved == True,
        )
        .all()
    )
    return [
        {
            "employee_id": m.employee_id,
            "department_id": m.department_id,
            "claim_type": m.claim_type,
            "claim_date": m.claim_date,
            "amount": m.amount,
        }
        for m in models
    ]
