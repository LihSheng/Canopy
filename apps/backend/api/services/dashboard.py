from sqlalchemy.orm import Session

from analytics.service import (
    get_claim_type_breakdown,
    get_dashboard_summary,
    get_monthly_trends,
    get_top_departments,
)
from anomalies.service import get_anomalies_list
from api.schemas.anomalies import AnomalyItem
from api.schemas.dashboard import (
    ClaimTypeBreakdownItem,
    DashboardCommandViewResponse,
    DashboardSummaryResponse,
    MonthlyTrendItem,
    PeriodInfo,
    TopDepartmentItem,
)


def get_dashboard_command_view(db: Session) -> DashboardCommandViewResponse:
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
