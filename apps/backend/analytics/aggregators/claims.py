from collections import defaultdict

from analytics.domain import MonthlyClaimTypeSpend, MonthlyDepartmentSpend


def aggregate_claims_by_department(
    snapshot_id: str,
    claim_rows: list[dict],
) -> list[MonthlyDepartmentSpend]:
    grouped: dict[tuple[str, str], dict[str, float | int]] = defaultdict(
        lambda: {"claims_total": 0.0, "claim_count": 0}
    )

    for row in claim_rows:
        dept_id = row.get("department_id") or "__unresolved__"
        month = _extract_month(row.get("claim_date", ""))
        amount = float(row.get("amount", 0))
        key = (dept_id, month)
        grouped[key]["claims_total"] = float(grouped[key]["claims_total"]) + amount
        grouped[key]["claim_count"] = int(grouped[key]["claim_count"]) + 1

    results: list[MonthlyDepartmentSpend] = []
    for (dept_id, month), values in grouped.items():
        claims = float(values["claims_total"])
        cc = int(values["claim_count"])
        results.append(
            MonthlyDepartmentSpend(
                id=_make_id(snapshot_id, "dept-claims", dept_id, month),
                snapshot_id=snapshot_id,
                department_id=dept_id,
                month=month,
                payroll_total=0.0,
                claims_total=claims,
                total=claims,
                claim_count=cc,
            )
        )

    return results


def aggregate_claims_by_employee(
    snapshot_id: str,
    claim_rows: list[dict],
) -> list[dict]:
    grouped: dict[tuple[str, str, str], dict[str, float | int]] = defaultdict(
        lambda: {"claims_total": 0.0, "claim_count": 0}
    )

    for row in claim_rows:
        emp_id = row.get("employee_id", "")
        dept_id = row.get("department_id") or "__unresolved__"
        month = _extract_month(row.get("claim_date", ""))
        amount = float(row.get("amount", 0))
        key = (emp_id, dept_id, month)
        grouped[key]["claims_total"] = float(grouped[key]["claims_total"]) + amount
        grouped[key]["claim_count"] = int(grouped[key]["claim_count"]) + 1

    return [
        {
            "employee_id": emp_id,
            "department_id": dept_id,
            "month": month,
            "claims_total": float(values["claims_total"]),
            "claim_count": int(values["claim_count"]),
        }
        for (emp_id, dept_id, month), values in grouped.items()
    ]


def aggregate_claims_by_type(
    snapshot_id: str,
    claim_rows: list[dict],
    department_id: str | None = None,
) -> list[MonthlyClaimTypeSpend]:
    filtered = claim_rows
    if department_id is not None:
        filtered = [r for r in claim_rows if r.get("department_id") == department_id]

    grouped: dict[tuple[str | None, str, str], dict[str, float | int]] = defaultdict(
        lambda: {"amount": 0.0, "claim_count": 0}
    )

    for row in filtered:
        dept_id = row.get("department_id") or "__unresolved__"
        claim_type = row.get("claim_type", "Other")
        month = _extract_month(row.get("claim_date", ""))
        amount = float(row.get("amount", 0))

        key_dept = department_id if department_id is not None else dept_id
        key = (key_dept, claim_type, month)
        grouped[key]["amount"] = float(grouped[key]["amount"]) + amount
        grouped[key]["claim_count"] = int(grouped[key]["claim_count"]) + 1

    results: list[MonthlyClaimTypeSpend] = []
    for (key_dept, claim_type, month), values in grouped.items():
        results.append(
            MonthlyClaimTypeSpend(
                id=_make_id(snapshot_id, "claim-type", key_dept or "org", claim_type, month),
                snapshot_id=snapshot_id,
                department_id=key_dept,
                claim_type=claim_type,
                month=month,
                amount=float(values["amount"]),
                claim_count=int(values["claim_count"]),
            )
        )

    return results


def _extract_month(date_str: str) -> str:
    if len(date_str) >= 7:
        return date_str[:7]
    return date_str


def _make_id(snapshot_id: str, prefix: str, *parts: str) -> str:
    import hashlib

    raw = f"{snapshot_id}:{prefix}:{':'.join(parts)}"
    return hashlib.md5(raw.encode()).hexdigest()
