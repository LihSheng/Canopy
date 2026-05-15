from sqlalchemy.orm import Session

from analytics.repositories.analytics import AnalyticsRepository
from analytics.service import (
    get_claim_type_breakdown,
    get_top_departments,
)
from anomalies.repository import AnomalyRepository
from insights.domain import (
    AnomalyFact,
    ClaimTypeFact,
    DepartmentRankingFact,
    FactBundle,
    TopDepartmentFact,
)


def extract_facts(db: Session) -> FactBundle | None:
    analytics_repo = AnalyticsRepository(db)
    cache = analytics_repo.get_latest_summary_cache()
    if cache is None:
        return None

    months = analytics_repo.get_distinct_months()
    current_month = months[0] if months else cache.month

    previous_month = months[1] if len(months) > 1 else None

    top_deps = get_top_departments(db)
    top_department_facts = [
        TopDepartmentFact(
            id=d.id,
            name=d.name,
            total_spend=d.total_spend,
            payroll_spend=d.payroll_spend,
            claims_spend=d.claims_spend,
            change_pct=d.change_pct,
        )
        for d in top_deps
    ]

    anomaly_repo = AnomalyRepository(db)
    anomaly_outputs = anomaly_repo.find_all(snapshot_id=cache.snapshot_id)
    dept_map = analytics_repo.get_department_map(cache.snapshot_id)

    anomaly_facts = [
        AnomalyFact(
            department_name=dept_map.get(a.target_entity_id, a.target_entity_id),
            severity=a.severity,
            description=a.description,
            change_pct=a.delta_percent,
        )
        for a in anomaly_outputs
    ]

    breakdown = get_claim_type_breakdown(db)
    claim_type_facts = [
        ClaimTypeFact(type=c.type, amount=c.amount, count=c.count)
        for c in breakdown
    ]

    department_spends = analytics_repo.get_monthly_spends_for_month(current_month)
    rankings = sorted(department_spends, key=lambda s: s.total, reverse=True)
    ranking_facts = [
        DepartmentRankingFact(
            name=dept_map.get(s.department_id, s.department_id),
            total_spend=s.total,
        )
        for s in rankings
    ]

    return FactBundle(
        snapshot_id=cache.snapshot_id,
        current_month=current_month,
        previous_month=previous_month,
        total_payroll=cache.total_payroll,
        total_claims=cache.total_claims,
        department_count=cache.department_count,
        anomaly_count=cache.anomaly_count,
        top_departments=top_department_facts,
        anomalies=anomaly_facts,
        claim_type_breakdown=claim_type_facts,
        department_rankings=ranking_facts,
    )
