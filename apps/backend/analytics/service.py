from datetime import datetime

from sqlalchemy.orm import Session

from analytics.aggregators.deltas import (
    attach_mom_deltas_to_rankings,
    calculate_mom_deltas,
    rank_departments,
)
from analytics.domain import (
    ClaimTypeBreakdown,
    DashboardSummary,
    DashboardSummaryCache,
    MonthlyDepartmentSpend,
    MonthlyTrend,
    TopDepartment,
)
from analytics.repositories.dashboard_cache import DashboardCacheRepository
from analytics.repositories.spend import SpendRepository


def get_dashboard_summary(db: Session) -> DashboardSummary:
    cache_repo = DashboardCacheRepository(db)
    cache = cache_repo.get_latest_summary_cache()

    if cache is None:
        now = datetime.now()
        return DashboardSummary(
            total_payroll=0.0,
            total_claims=0.0,
            year=now.year,
            month=now.month,
            department_count=0,
            anomaly_count=0,
            last_updated="",
            snapshot_id="",
        )

    return _cache_to_summary(cache)


def get_monthly_trends(
    db: Session,
    year: int | None = None,
    month: int | None = None,
) -> list[MonthlyTrend]:
    spend_repo = SpendRepository(db)
    spends = spend_repo.get_all_monthly_spends()

    month_totals: dict[str, dict[str, float]] = {}
    for s in spends:
        if s.month not in month_totals:
            month_totals[s.month] = {"payroll": 0.0, "claims": 0.0}
        month_totals[s.month]["payroll"] += s.payroll_total
        month_totals[s.month]["claims"] += s.claims_total

    trends: list[MonthlyTrend] = []
    for m_key in sorted(month_totals.keys()):
        values = month_totals[m_key]
        trends.append(
            MonthlyTrend(
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


def get_top_departments(db: Session) -> list[TopDepartment]:
    spend_repo = SpendRepository(db)
    months = spend_repo.get_distinct_months()

    if not months:
        return []

    current_month = months[0]
    snapshot_id = spend_repo.get_snapshot_id_from_aggregates() or ""
    spends = spend_repo.get_monthly_spends_for_month(current_month)
    names = spend_repo.get_department_map(snapshot_id)

    rankings = rank_departments(spends, current_month, names)

    previous_month = months[1] if len(months) > 1 else None
    if previous_month:
        previous_spends_raw = spend_repo.get_monthly_spends_for_month(previous_month)
        deltas = calculate_mom_deltas(
            snapshot_id=snapshot_id,
            spends=list(spends) + list(previous_spends_raw),
            current_month=current_month,
            previous_month=previous_month,
        )
        attach_mom_deltas_to_rankings(rankings, deltas)

    top5 = rankings[:5]
    return [
        TopDepartment(
            id=r.department_id,
            name=r.department_name,
            total_spend=r.total_spend,
            payroll_spend=r.payroll_spend,
            claims_spend=r.claims_spend,
            change_pct=r.change_pct,
        )
        for r in top5
    ]


def get_claim_type_breakdown(db: Session) -> list[ClaimTypeBreakdown]:
    spend_repo = SpendRepository(db)
    months = spend_repo.get_distinct_months()

    if not months:
        return []

    current_month = months[0]
    spends = spend_repo.get_claim_type_spends(month=current_month)

    type_totals: dict[str, dict[str, float | int]] = {}
    for s in spends:
        if s.claim_type not in type_totals:
            type_totals[s.claim_type] = {"amount": 0.0, "count": 0}
        type_totals[s.claim_type]["amount"] = float(type_totals[s.claim_type]["amount"]) + s.amount
        type_totals[s.claim_type]["count"] = int(type_totals[s.claim_type]["count"]) + s.claim_count

    sorted_types = sorted(type_totals.items(), key=lambda x: float(x[1]["amount"]), reverse=True)

    return [
        ClaimTypeBreakdown(
            type=claim_type,
            amount=float(values["amount"]),
            count=int(values["count"]),
        )
        for claim_type, values in sorted_types
    ]


def get_distinct_months(db: Session, snapshot_id: str | None = None) -> list[str]:
    spend_repo = SpendRepository(db)
    return spend_repo.get_distinct_months(snapshot_id=snapshot_id)


def get_department_map(db: Session, snapshot_id: str | None = None) -> dict[str, str]:
    spend_repo = SpendRepository(db)
    return spend_repo.get_department_map(snapshot_id=snapshot_id)


def get_monthly_spends_for_month(
    db: Session, month: str, snapshot_id: str | None = None
) -> list[MonthlyDepartmentSpend]:
    spend_repo = SpendRepository(db)
    return spend_repo.get_monthly_spends_for_month(month, snapshot_id=snapshot_id)


def get_all_monthly_spends(db: Session, snapshot_id: str | None = None) -> list[MonthlyDepartmentSpend]:
    spend_repo = SpendRepository(db)
    return spend_repo.get_all_monthly_spends(snapshot_id=snapshot_id)


def get_snapshot_id_from_aggregates(db: Session) -> str | None:
    spend_repo = SpendRepository(db)
    return spend_repo.get_snapshot_id_from_aggregates()


def _cache_to_summary(cache: DashboardSummaryCache) -> DashboardSummary:
    return DashboardSummary(
        total_payroll=cache.total_payroll,
        total_claims=cache.total_claims,
        year=cache.year,
        month=cache.month,
        department_count=cache.department_count,
        anomaly_count=cache.anomaly_count,
        last_updated=cache.created_at,
        snapshot_id=cache.snapshot_id,
    )


def get_summary_cache_for_snapshot(db: Session, snapshot_id: str) -> DashboardSummary | None:
    cache_repo = DashboardCacheRepository(db)
    cache = cache_repo.get_summary_cache_for_snapshot(snapshot_id)
    if cache is None:
        return None
    return _cache_to_summary(cache)
