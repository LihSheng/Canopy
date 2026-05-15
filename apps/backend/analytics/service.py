from datetime import datetime

from sqlalchemy.orm import Session

from analytics.aggregators.deltas import (
    attach_mom_deltas_to_rankings,
    calculate_mom_deltas,
    rank_departments,
)
from analytics.repositories.analytics import AnalyticsRepository
from api.schemas.dashboard import (
    ClaimTypeBreakdownItem,
    DashboardSummaryResponse,
    MonthlyTrendItem,
    PeriodInfo,
    TopDepartmentItem,
)


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    repo = AnalyticsRepository(db)
    cache = repo.get_latest_summary_cache()

    if cache is None:
        return DashboardSummaryResponse(
            total_payroll=0.0,
            total_claims=0.0,
            period=PeriodInfo(year=datetime.now().year, month=datetime.now().month),
            department_count=0,
            anomaly_count=0,
            last_updated="",
        )

    return DashboardSummaryResponse(
        total_payroll=cache.total_payroll,
        total_claims=cache.total_claims,
        period=PeriodInfo(year=cache.year, month=cache.month),
        department_count=cache.department_count,
        anomaly_count=cache.anomaly_count,
        last_updated=cache.created_at,
    )


def get_monthly_trends(
    db: Session,
    year: int | None = None,
    month: int | None = None,
) -> list[MonthlyTrendItem]:
    repo = AnalyticsRepository(db)
    spends = repo.get_all_monthly_spends()

    month_totals: dict[str, dict[str, float]] = {}
    for s in spends:
        if s.month not in month_totals:
            month_totals[s.month] = {"payroll": 0.0, "claims": 0.0}
        month_totals[s.month]["payroll"] += s.payroll_total
        month_totals[s.month]["claims"] += s.claims_total

    trends: list[MonthlyTrendItem] = []
    for m_key in sorted(month_totals.keys()):
        values = month_totals[m_key]
        trends.append(
            MonthlyTrendItem(
                month=m_key,
                payroll=round(values["payroll"], 2),
                claims=round(values["claims"], 2),
                total=round(values["payroll"] + values["claims"], 2),
            )
        )

    if year is not None and month is not None:
        target = f"{year:04d}-{month:02d}"
        trends = [t for t in trends if t.month == target]

    return trends


def get_top_departments(db: Session) -> list[TopDepartmentItem]:
    repo = AnalyticsRepository(db)
    months = repo.get_distinct_months()

    if not months:
        return []

    current_month = months[0]
    snapshot_id = repo.get_snapshot_id_from_aggregates() or ""
    spends = repo.get_monthly_spends_for_month(current_month)
    names = repo.get_department_map(snapshot_id)

    rankings = rank_departments(spends, current_month, names)

    previous_month = months[1] if len(months) > 1 else None
    if previous_month:
        previous_spends_raw = repo.get_monthly_spends_for_month(previous_month)
        deltas = calculate_mom_deltas(
            snapshot_id=snapshot_id,
            spends=list(spends) + list(previous_spends_raw),
            current_month=current_month,
            previous_month=previous_month,
        )
        attach_mom_deltas_to_rankings(rankings, deltas)

    top5 = rankings[:5]
    return [
        TopDepartmentItem(
            id=r.department_id,
            name=r.department_name,
            total_spend=r.total_spend,
            payroll_spend=r.payroll_spend,
            claims_spend=r.claims_spend,
            change_pct=r.change_pct,
        )
        for r in top5
    ]


def get_claim_type_breakdown(db: Session) -> list[ClaimTypeBreakdownItem]:
    repo = AnalyticsRepository(db)
    months = repo.get_distinct_months()

    if not months:
        return []

    current_month = months[0]
    spends = repo.get_claim_type_spends(month=current_month)

    type_totals: dict[str, dict[str, float | int]] = {}
    for s in spends:
        if s.claim_type not in type_totals:
            type_totals[s.claim_type] = {"amount": 0.0, "count": 0}
        type_totals[s.claim_type]["amount"] = float(type_totals[s.claim_type]["amount"]) + s.amount
        type_totals[s.claim_type]["count"] = int(type_totals[s.claim_type]["count"]) + s.claim_count

    sorted_types = sorted(type_totals.items(), key=lambda x: float(x[1]["amount"]), reverse=True)

    return [
        ClaimTypeBreakdownItem(
            type=claim_type,
            amount=float(values["amount"]),
            count=int(values["count"]),
        )
        for claim_type, values in sorted_types
    ]
