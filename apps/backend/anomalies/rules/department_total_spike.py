import uuid

from analytics.domain import MonthlyDepartmentSpend
from anomalies.domain import AnomalyOutput
from anomalies.severity import classify_severity


def department_total_spike_rule(
    snapshot_id: str,
    current_spends: list[MonthlyDepartmentSpend],
    previous_spends: list[MonthlyDepartmentSpend],
    threshold_pct: float = 0.0,
) -> list[AnomalyOutput]:
    anomaly_type = "department_total_spike"
    prev_by_dept: dict[str, float] = {s.department_id: s.total for s in previous_spends}
    cur_by_dept: dict[str, MonthlyDepartmentSpend] = {s.department_id: s for s in current_spends}

    results: list[AnomalyOutput] = []
    effective_threshold = threshold_pct if threshold_pct else 7.5

    for dept_id, cur_spend in cur_by_dept.items():
        prev_total = prev_by_dept.get(dept_id, 0.0)
        cur_total = cur_spend.total

        if prev_total == 0.0:
            continue

        delta = round(cur_total - prev_total, 2)
        delta_pct = round((delta / prev_total) * 100, 2)

        if abs(delta_pct) < effective_threshold:
            continue

        severity = classify_severity(delta_pct)
        direction = "increased" if delta > 0 else "decreased"
        description = (
            f"Department total spend {direction} {abs(delta_pct):.1f}% "
            f"month-over-month, driven by "
            f"{_dominant_category(cur_spend)} changes."
        )

        driver_details = _build_drivers(cur_spend, prev_total)

        results.append(
            AnomalyOutput(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot_id,
                anomaly_type=anomaly_type,
                target_entity_type="department",
                target_entity_id=dept_id,
                month_key=cur_spend.month,
                baseline_value=prev_total,
                observed_value=cur_total,
                delta_value=delta,
                delta_percent=delta_pct,
                severity=severity,
                driver_details=driver_details,
                description=description,
            )
        )

    return results


def _dominant_category(spend: MonthlyDepartmentSpend) -> str:
    return "payroll" if spend.payroll_total >= spend.claims_total else "claims"


def _build_drivers(spend: MonthlyDepartmentSpend, prev_total: float) -> list[str]:
    drivers: list[str] = []
    if spend.payroll_total > 0:
        payroll_share = round((spend.payroll_total / spend.total) * 100, 1) if spend.total else 0
        drivers.append(f"Payroll: {spend.payroll_total:.0f} MYR ({payroll_share}% of total)")
    if spend.claims_total > 0:
        claims_share = round((spend.claims_total / spend.total) * 100, 1) if spend.total else 0
        drivers.append(f"Claims: {spend.claims_total:.0f} MYR ({claims_share}% of total, {spend.claim_count} claims)")
    drivers.append(f"Previous month total: {prev_total:.0f} MYR")
    return drivers
