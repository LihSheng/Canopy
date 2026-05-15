from collections import defaultdict

from analytics.domain import MonthlyDepartmentSpend, MonthlyEmployeeSpend


def merge_department_spend(
    snapshot_id: str,
    payroll_spends: list[MonthlyDepartmentSpend],
    claims_spends: list[MonthlyDepartmentSpend],
) -> list[MonthlyDepartmentSpend]:
    merged: dict[tuple[str, str], dict[str, float | int]] = defaultdict(
        lambda: {"payroll_total": 0.0, "claims_total": 0.0, "claim_count": 0}
    )

    _ingest(merged, payroll_spends)
    _ingest(merged, claims_spends)

    results: list[MonthlyDepartmentSpend] = []
    for (dept_id, month), values in merged.items():
        payroll = float(values["payroll_total"])
        claims = float(values["claims_total"])
        cc = int(values["claim_count"])
        results.append(
            MonthlyDepartmentSpend(
                id=_make_id(snapshot_id, "dept-merged", dept_id, month),
                snapshot_id=snapshot_id,
                department_id=dept_id,
                month=month,
                payroll_total=payroll,
                claims_total=claims,
                total=payroll + claims,
                claim_count=cc,
            )
        )

    return results


def merge_employee_spend(
    snapshot_id: str,
    payroll_rows: list[dict],
    claims_rows: list[dict],
) -> list[MonthlyEmployeeSpend]:
    grouped: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: {"payroll_total": 0.0, "claims_total": 0.0}
    )

    for row in payroll_rows:
        key = (row["employee_id"], row["department_id"], row["month"])
        grouped[key]["payroll_total"] += row["payroll_total"]

    for row in claims_rows:
        key = (row["employee_id"], row["department_id"], row["month"])
        grouped[key]["claims_total"] += row["claims_total"]

    results: list[MonthlyEmployeeSpend] = []
    for (emp_id, dept_id, month), values in grouped.items():
        payroll = values["payroll_total"]
        claims = values["claims_total"]
        results.append(
            MonthlyEmployeeSpend(
                id=_make_id(snapshot_id, "emp-merged", emp_id, dept_id, month),
                snapshot_id=snapshot_id,
                employee_id=emp_id,
                department_id=dept_id,
                month=month,
                payroll_total=payroll,
                claims_total=claims,
                total=payroll + claims,
            )
        )

    return results


def _ingest(
    merged: dict[tuple[str, str], dict[str, float | int]],
    spends: list[MonthlyDepartmentSpend],
) -> None:
    for s in spends:
        key = (s.department_id, s.month)
        merged[key]["payroll_total"] = float(merged[key]["payroll_total"]) + s.payroll_total
        merged[key]["claims_total"] = float(merged[key]["claims_total"]) + s.claims_total
        merged[key]["claim_count"] = int(merged[key]["claim_count"]) + s.claim_count


def _make_id(snapshot_id: str, prefix: str, *parts: str) -> str:
    import hashlib

    raw = f"{snapshot_id}:{prefix}:{':'.join(parts)}"
    return hashlib.md5(raw.encode()).hexdigest()
