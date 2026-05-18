from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics.departments import (
    get_claims,
    get_department,
    get_department_claim_types,
    get_department_employees,
    get_department_trends,
)
from analytics.departments import (
    get_departments as get_all_departments,
)
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.departments import (
    ClaimDetailItem,
    DepartmentClaimTypeItem,
    DepartmentDetailResponse,
    DepartmentItem,
    EmployeeContributionItem,
)
from api.schemas.dashboard import MonthlyTrendItem
from common.database import get_db
from common.errors import NotFoundError

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("")
def list_departments(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    sort_by: str | None = Query(default=None, description="Sort: total_spend, change_pct, attention"),
):
    departments = get_all_departments(db, sort_by=sort_by)
    return [
        DepartmentItem(
            id=d.id,
            name=d.name,
            total_spend=d.total_spend,
            payroll_spend=d.payroll_spend,
            claims_spend=d.claims_spend,
            change_pct=d.change_pct,
        )
        for d in departments
    ]


@router.get("/{department_id}", response_model=DepartmentDetailResponse)
def department_detail(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_department(db, department_id)
    if result is None:
        raise NotFoundError("Department not found")
    return DepartmentDetailResponse(
        id=result.id,
        name=result.name,
        total_spend=result.total_spend,
        payroll_spend=result.payroll_spend,
        claims_spend=result.claims_spend,
        change_pct=result.change_pct,
        employee_count=result.employee_count,
        attention_state=result.attention_state,
        ai_summary=result.ai_summary,
    )


@router.get("/{department_id}/trends")
def department_trends(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    trends = get_department_trends(db, department_id)
    return [
        MonthlyTrendItem(
            month=t.month,
            payroll=t.payroll,
            claims=t.claims,
            total=t.total,
        )
        for t in trends
    ]


@router.get("/{department_id}/employees")
def department_employees(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    employees = get_department_employees(db, department_id)
    return [
        EmployeeContributionItem(
            id=e.id,
            name=e.name,
            department=e.department,
            payroll=e.payroll,
            claims=e.claims,
            total=e.total,
        )
        for e in employees
    ]


@router.get("/{department_id}/claim-types")
def department_claim_types(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    claim_types = get_department_claim_types(db, department_id)
    return [
        DepartmentClaimTypeItem(
            type=c.type,
            amount=c.amount,
            count=c.count,
        )
        for c in claim_types
    ]


@router.get("/{department_id}/claims")
def department_claims(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    claims = get_claims(db, department_id=department_id)
    return [
        ClaimDetailItem(
            id=c.id,
            employee_name=c.employee_name,
            department=c.department,
            type=c.type,
            amount=c.amount,
            date=c.date,
        )
        for c in claims
    ]
