import uuid

from analytics.domain import MonthlyDepartmentSpend
from anomalies.domain import AnomalyOutput
from anomalies.severity import classify_severity


def department_claim_spike_rule(
    snapshot_id: str,
    current_spends: list[MonthlyDepartmentSpend],
    previous_spends: list[MonthlyDepartmentSpend],
    threshold_pct: float = 0.0,
) -> list[AnomalyOutput]:
    anomaly_type = "department_claim_spike"
    prev_by_dept: dict[str, float] = {s.department_id: s.claims_total for s in previous_spends}
    cur_by_dept: dict[str, MonthlyDepartmentSpend] = {s.department_id: s for s in current_spends}

    results: list[AnomalyOutput] = []
    effective_threshold = threshold_pct if threshold_pct else 10.0

    for dept_id, cur_spend in cur_by_dept.items():
        prev_claims = prev_by_dept.get(dept_id, 0.0)
        cur_claims = cur_spend.claims_total

        if prev_claims == 0.0 and cur_claims == 0.0:
            continue

        if prev_claims == 0.0:
            if cur_claims > 0:
                delta_pct = 100.0
                delta = cur_claims
            else:
                continue
        else:
            delta = round(cur_claims - prev_claims, 2)
            delta_pct = round((delta / prev_claims) * 100, 2)

        if abs(delta_pct) < effective_threshold:
            continue

        severity = classify_severity(delta_pct)
        direction = "increased" if delta > 0 else "decreased"
        description = (
            f"Department claims spend {direction} {abs(delta_pct):.1f}% "
            f"month-over-month ({cur_spend.claim_count} claims in current month)."
        )

        driver_details = _build_drivers(cur_spend, prev_claims)

        results.append(
            AnomalyOutput(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot_id,
                anomaly_type=anomaly_type,
                target_entity_type="department",
                target_entity_id=dept_id,
                month_key=cur_spend.month,
                baseline_value=prev_claims,
                observed_value=cur_claims,
                delta_value=delta,
                delta_percent=delta_pct,
                severity=severity,
                driver_details=driver_details,
                description=description,
            )
        )

    return results


def _build_drivers(spend: MonthlyDepartmentSpend, prev_claims: float) -> list[str]:
    drivers: list[str] = []
    drivers.append(f"Current claims: {spend.claims_total:.0f} MYR ({spend.claim_count} claims)")
    drivers.append(f"Previous month claims: {prev_claims:.0f} MYR")
    if spend.payroll_total > 0 and spend.total > 0:
        claims_share = round((spend.claims_total / spend.total) * 100, 1)
        drivers.append(f"Claims represent {claims_share}% of department total spend")
    return drivers
