from sqlalchemy.orm import Session

from analytics.aggregators.deltas import (
    attach_mom_deltas_to_rankings,
    calculate_mom_deltas,
    rank_departments,
)
from analytics.domain import (
    ClaimDetail,
    DepartmentClaimType,
    DepartmentDetail,
    DepartmentSummary,
    EmployeeContribution,
    MonthlyTrend,
)
from analytics.repositories.spend import SpendRepository


def get_departments(
    db: Session,
    sort_by: str | None = None,
    snapshot_id: str | None = None,
) -> list[DepartmentSummary]:
    repo = SpendRepository(db)
    months = repo.get_distinct_months(snapshot_id=snapshot_id)

    if not months:
        return []

    current_month = months[0]
    snapshot_id = snapshot_id or repo.get_snapshot_id_from_aggregates() or ""
    spends = repo.get_monthly_spends_for_month(current_month, snapshot_id=snapshot_id)
    names = repo.get_department_map(snapshot_id)

    rankings = rank_departments(spends, current_month, names)

    previous_month = months[1] if len(months) > 1 else None
    if previous_month:
        previous_spends_raw = repo.get_monthly_spends_for_month(
            previous_month,
            snapshot_id=snapshot_id,
        )
        deltas = calculate_mom_deltas(
            snapshot_id=snapshot_id,
            spends=list(spends) + list(previous_spends_raw),
            current_month=current_month,
            previous_month=previous_month,
        )
        attach_mom_deltas_to_rankings(rankings, deltas)

    items = [
        DepartmentSummary(
            id=r.department_id,
            name=r.department_name,
            total_spend=r.total_spend,
            payroll_spend=r.payroll_spend,
            claims_spend=r.claims_spend,
            change_pct=r.change_pct,
        )
        for r in rankings
    ]

    if sort_by == "change_pct":
        items.sort(key=lambda d: abs(d.change_pct), reverse=True)
    elif sort_by == "attention":
        items.sort(key=lambda d: (abs(d.change_pct), d.total_spend), reverse=True)
    elif sort_by == "total_spend":
        items.sort(key=lambda d: d.total_spend, reverse=True)

    return items


def get_department(db: Session, department_id: str) -> DepartmentDetail | None:
    repo = SpendRepository(db)
    months = repo.get_distinct_months()
    snapshot_id = repo.get_snapshot_id_from_aggregates() or ""
    names = repo.get_department_map(snapshot_id)

    if department_id not in names:
        return None

    department_name = names[department_id]

    if not months:
        return DepartmentDetail(
            id=department_id,
            name=department_name,
            total_spend=0.0,
            payroll_spend=0.0,
            claims_spend=0.0,
            change_pct=0.0,
            employee_count=0,
        )

    current_month = months[0]
    spends = repo.get_monthly_spends_for_month(current_month)

    dept_spend = next((s for s in spends if s.department_id == department_id), None)

    total_spend = dept_spend.total if dept_spend else 0.0
    payroll_spend = dept_spend.payroll_total if dept_spend else 0.0
    claims_spend = dept_spend.claims_total if dept_spend else 0.0

    change_pct = 0.0
    previous_month = months[1] if len(months) > 1 else None
    if previous_month:
        prev_spends = repo.get_monthly_spends_for_month(previous_month)
        prev_dept = next((s for s in prev_spends if s.department_id == department_id), None)
        if prev_dept and prev_dept.total != 0:
            change_pct = round(((total_spend - prev_dept.total) / prev_dept.total) * 100, 2)

    employees = repo.get_employee_spends_for_department(department_id, month=current_month)

    return DepartmentDetail(
        id=department_id,
        name=department_name,
        total_spend=total_spend,
        payroll_spend=payroll_spend,
        claims_spend=claims_spend,
        change_pct=change_pct,
        employee_count=len(employees),
    )


def get_department_employees(db: Session, department_id: str) -> list[EmployeeContribution]:
    repo = SpendRepository(db)
    months = repo.get_distinct_months()

    if not months:
        return []

    current_month = months[0]
    contributions = repo.get_employee_contributions(department_id, month=current_month)

    return [
        EmployeeContribution(
            id=c.employee_id,
            name=c.employee_name,
            department=c.department_name,
            payroll=c.payroll,
            claims=c.claims,
            total=c.total,
        )
        for c in contributions
    ]


def get_department_trends(db: Session, department_id: str) -> list[MonthlyTrend]:
    repo = SpendRepository(db)
    spends = repo.get_monthly_spends_for_department(department_id)

    return [
        MonthlyTrend(
            month=s.month,
            payroll=round(s.payroll_total, 2),
            claims=round(s.claims_total, 2),
            total=round(s.total, 2),
        )
        for s in spends
    ]


def get_department_claim_types(db: Session, department_id: str) -> list[DepartmentClaimType]:
    repo = SpendRepository(db)
    months = repo.get_distinct_months()

    if not months:
        return []

    current_month = months[0]
    type_spends = repo.get_claim_type_spends(department_id=department_id, month=current_month)

    return [
        DepartmentClaimType(
            type=s.claim_type,
            amount=s.amount,
            count=s.claim_count,
        )
        for s in type_spends
    ]


def get_claims(db: Session, department_id: str | None = None) -> list[ClaimDetail]:
    repo = SpendRepository(db)
    details = repo.get_claim_details(department_id=department_id)

    return [
        ClaimDetail(
            id=c.claim_id,
            employee_name=c.employee_name,
            department=c.department_name,
            type=c.claim_type,
            amount=c.amount,
            date=c.claim_date,
        )
        for c in details
    ]
