from collections.abc import Sequence

from analytics.domain import DepartmentMoMDelta, DepartmentRanking, MonthlyDepartmentSpend


def calculate_mom_deltas(
    snapshot_id: str,
    spends: Sequence[MonthlyDepartmentSpend],
    current_month: str,
    previous_month: str,
) -> list[DepartmentMoMDelta]:
    current_by_dept: dict[str, float] = {}
    previous_by_dept: dict[str, float] = {}

    for s in spends:
        if s.month == current_month:
            current_by_dept[s.department_id] = s.total
        if s.month == previous_month:
            previous_by_dept[s.department_id] = s.total

    deltas: list[DepartmentMoMDelta] = []
    all_depts = set(current_by_dept.keys()) | set(previous_by_dept.keys())

    for dept_id in sorted(all_depts):
        current = current_by_dept.get(dept_id, 0.0)
        previous = previous_by_dept.get(dept_id, 0.0)
        change = current - previous

        if previous != 0:
            change_pct = round((change / previous) * 100, 2)
        else:
            change_pct = 0.0

        deltas.append(
            DepartmentMoMDelta(
                snapshot_id=snapshot_id,
                department_id=dept_id,
                current_month=current_month,
                previous_month=previous_month,
                current_total=current,
                previous_total=previous,
                total_change=change,
                total_change_pct=change_pct,
            )
        )

    return deltas


def rank_departments(
    spends: Sequence[MonthlyDepartmentSpend],
    month: str,
    department_names: dict[str, str] | None = None,
) -> list[DepartmentRanking]:
    dept_totals: dict[str, dict[str, float]] = {}
    for s in spends:
        if s.month != month:
            continue
        dept_totals[s.department_id] = {
            "total_spend": s.total,
            "payroll_spend": s.payroll_total,
            "claims_spend": s.claims_total,
        }

    sorted_depts = sorted(dept_totals.items(), key=lambda x: x[1]["total_spend"], reverse=True)

    names = department_names or {}
    rankings: list[DepartmentRanking] = []
    for rank_idx, (dept_id, values) in enumerate(sorted_depts):
        rankings.append(
            DepartmentRanking(
                snapshot_id=spends[0].snapshot_id if spends else "",
                department_id=dept_id,
                department_name=names.get(dept_id, dept_id),
                month=month,
                total_spend=values["total_spend"],
                payroll_spend=values["payroll_spend"],
                claims_spend=values["claims_spend"],
                rank=rank_idx + 1,
                change_pct=0.0,
            )
        )

    return rankings


def attach_mom_deltas_to_rankings(
    rankings: list[DepartmentRanking],
    deltas: Sequence[DepartmentMoMDelta],
) -> list[DepartmentRanking]:
    delta_map: dict[str, float] = {d.department_id: d.total_change_pct for d in deltas}
    for r in rankings:
        r.change_pct = delta_map.get(r.department_id, 0.0)
    return rankings
