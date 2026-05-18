from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics.service import (
    get_claim_type_breakdown,
    get_dashboard_summary,
    get_monthly_trends,
    get_top_departments,
)
from anomalies.service import get_anomalies_list
from api.dependencies.auth import get_current_user
from api.schemas.anomalies import AnomalyItem
from api.schemas.auth import SessionUser
from api.schemas.dashboard import (
    ClaimTypeBreakdownItem,
    DashboardCommandViewResponse,
    DashboardSummaryResponse,
    MonthlyTrendItem,
    PeriodInfo,
    TopDepartmentItem,
)
from common.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    summary = get_dashboard_summary(db)
    return DashboardSummaryResponse(
        total_payroll=summary.total_payroll,
        total_claims=summary.total_claims,
        period=PeriodInfo(year=summary.year, month=summary.month),
        department_count=summary.department_count,
        anomaly_count=summary.anomaly_count,
        last_updated=summary.last_updated,
    )


@router.get("/trends")
def dashboard_trends(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    trends = get_monthly_trends(db, year=year, month=month)
    return [
        MonthlyTrendItem(
            month=t.month,
            payroll=t.payroll,
            claims=t.claims,
            total=t.total,
        )
        for t in trends
    ]


@router.get("/top-departments")
def dashboard_top_departments(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    departments = get_top_departments(db)
    return [
        TopDepartmentItem(
            id=d.id,
            name=d.name,
            total_spend=d.total_spend,
            payroll_spend=d.payroll_spend,
            claims_spend=d.claims_spend,
            change_pct=d.change_pct,
        )
        for d in departments
    ]


@router.get("/claim-types")
def dashboard_claim_types(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    claim_types = get_claim_type_breakdown(db)
    return [
        ClaimTypeBreakdownItem(
            type=c.type,
            amount=c.amount,
            count=c.count,
        )
        for c in claim_types
    ]


@router.get("/command-view", response_model=DashboardCommandViewResponse)
def dashboard_command_view(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    summary = get_dashboard_summary(db)
    departments = get_top_departments(db)
    trends = get_monthly_trends(db)
    claim_types = get_claim_type_breakdown(db)
    anomalies_raw = get_anomalies_list(db)
    anomalies = [AnomalyItem(**a) for a in anomalies_raw]
    return DashboardCommandViewResponse(
        summary=DashboardSummaryResponse(
            total_payroll=summary.total_payroll,
            total_claims=summary.total_claims,
            period=PeriodInfo(year=summary.year, month=summary.month),
            department_count=summary.department_count,
            anomaly_count=summary.anomaly_count,
            last_updated=summary.last_updated,
        ),
        departments=[
            TopDepartmentItem(
                id=d.id,
                name=d.name,
                total_spend=d.total_spend,
                payroll_spend=d.payroll_spend,
                claims_spend=d.claims_spend,
                change_pct=d.change_pct,
            )
            for d in departments
        ],
        trends=[
            MonthlyTrendItem(
                month=t.month,
                payroll=t.payroll,
                claims=t.claims,
                total=t.total,
            )
            for t in trends
        ],
        claim_types=[
            ClaimTypeBreakdownItem(
                type=c.type,
                amount=c.amount,
                count=c.count,
            )
            for c in claim_types
        ],
        anomalies=anomalies,
    )
