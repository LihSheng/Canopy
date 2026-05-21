from sqlalchemy.orm import Session

from analytics.service import (
    get_claim_type_breakdown,
    get_dashboard_summary,
    get_department_map,
    get_distinct_months,
    get_monthly_spends_for_month,
    get_top_departments,
)
from anomalies.service import get_anomalies_list
from insights.domain import (
    AnomalyFact,
    ClaimTypeFact,
    DepartmentRankingFact,
    FactBundle,
    TopDepartmentFact,
)


def extract_facts(db: Session) -> FactBundle | None:
    summary = get_dashboard_summary(db)
    if not summary or not summary.last_updated:
        return None

    months = get_distinct_months(db)
    current_month = months[0] if months else f"{summary.year:04d}-{summary.month:02d}"
    previous_month = months[1] if len(months) > 1 else None

    snapshot_id = summary.snapshot_id

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

    anomaly_outputs = get_anomalies_list(db, snapshot_id=snapshot_id)
    dept_map = get_department_map(db, snapshot_id=snapshot_id)

    anomaly_facts = [
        AnomalyFact(
            department_name=dept_map.get(a.get("department_id", ""), a.get("department_id", "")),
            severity=a.get("severity", "low"),
            description=a.get("description", ""),
            change_pct=a.get("change_pct", 0.0),
        )
        for a in anomaly_outputs
    ]

    breakdown = get_claim_type_breakdown(db)
    claim_type_facts = [ClaimTypeFact(type=c.type, amount=c.amount, count=c.count) for c in breakdown]

    department_spends = get_monthly_spends_for_month(db, current_month, snapshot_id=snapshot_id)
    rankings = sorted(department_spends, key=lambda s: s.total, reverse=True)
    ranking_facts = [
        DepartmentRankingFact(
            name=dept_map.get(s.department_id, s.department_id),
            total_spend=s.total,
        )
        for s in rankings
    ]

    return FactBundle(
        snapshot_id=snapshot_id,
        current_month=current_month,
        previous_month=previous_month,
        total_payroll=summary.total_payroll,
        total_claims=summary.total_claims,
        department_count=summary.department_count,
        anomaly_count=summary.anomaly_count,
        top_departments=top_department_facts,
        anomalies=anomaly_facts,
        claim_type_breakdown=claim_type_facts,
        department_rankings=ranking_facts,
    )
