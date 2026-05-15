from collections import defaultdict

from analytics.domain import MonthlyDepartmentSpend


def aggregate_payroll_by_department(
    snapshot_id: str,
    payroll_rows: list[dict],
) -> list[MonthlyDepartmentSpend]:
    grouped: dict[tuple[str, str], dict[str, float | int]] = defaultdict(
        lambda: {"payroll_total": 0.0, "claims_total": 0.0, "claim_count": 0}
    )

    for row in payroll_rows:
        dept_id = row.get("department_id") or "__unresolved__"
        month = row.get("payroll_month", "")
        amount = float(row.get("amount", 0))
        key = (dept_id, month)
        grouped[key]["payroll_total"] = float(grouped[key]["payroll_total"]) + amount

    results: list[MonthlyDepartmentSpend] = []
    for (dept_id, month), values in grouped.items():
        payroll = float(values["payroll_total"])
        claims = float(values["claims_total"])
        cc = int(values["claim_count"])
        results.append(
            MonthlyDepartmentSpend(
                id=_make_id(snapshot_id, "dept", dept_id, month),
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


def aggregate_payroll_by_employee(
    snapshot_id: str,
    payroll_rows: list[dict],
) -> list[dict]:
    grouped: dict[tuple[str, str, str], float] = defaultdict(float)

    for row in payroll_rows:
        emp_id = row.get("employee_id", "")
        dept_id = row.get("department_id") or "__unresolved__"
        month = row.get("payroll_month", "")
        amount = float(row.get("amount", 0))
        grouped[(emp_id, dept_id, month)] += amount

    return [
        {
            "employee_id": emp_id,
            "department_id": dept_id,
            "month": month,
            "payroll_total": total,
        }
        for (emp_id, dept_id, month), total in grouped.items()
    ]


def _make_id(snapshot_id: str, prefix: str, *parts: str) -> str:
    import hashlib

    raw = f"{snapshot_id}:{prefix}:{':'.join(parts)}"
    return hashlib.md5(raw.encode()).hexdigest()
