"""Export payload construction — snapshot context, department/anomaly/trend collection.

Split from exports.service to separate payload-building concern from
job management and background execution.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from analytics.departments import get_departments as get_departments_list
from analytics.service import (
    get_all_monthly_spends,
    get_dashboard_summary,
    get_department_map,
    get_distinct_months,
    get_snapshot_id_from_aggregates,
    get_summary_cache_for_snapshot,
)
from anomalies.service import get_anomalies_list
from common.clock import iso_now
from common.database import session_factory
from exports.domain import (
    AnomalyExportRow,
    DepartmentExportRow,
    ExportPayload,
    MonthlyTrendExportRow,
)


@dataclass(frozen=True)
class SnapshotContext:
    snapshot_id: str
    period_label: str
    total_payroll: float
    total_claims: float
    department_count: int
    anomaly_count: int
    created_at: str


def _get_snapshot_context(
    db: Session | None = None,
    snapshot_id: str | None = None,
) -> SnapshotContext | None:
    owns_db = db is None
    db = db or session_factory()()
    try:
        summary = get_summary_cache_for_snapshot(db, snapshot_id) if snapshot_id else get_dashboard_summary(db)
        if summary is None:
            return None
        return SnapshotContext(
            snapshot_id=summary.snapshot_id,
            period_label=f"{summary.year:04d}-{summary.month:02d}",
            total_payroll=summary.total_payroll,
            total_claims=summary.total_claims,
            department_count=summary.department_count,
            anomaly_count=summary.anomaly_count,
            created_at=summary.last_updated,
        )
    finally:
        if owns_db:
            db.close()


def _get_snapshot_id(db: Session) -> str | None:
    try:
        return get_snapshot_id_from_aggregates(db)
    except Exception:
        return None


def _allowed_months(
    db: Session,
    snapshot_id: str,
    period_label: str,
    time_range: str,
) -> list[str]:
    months = get_distinct_months(db, snapshot_id=snapshot_id)
    if not months:
        return []
    if time_range == "all":
        return months

    latest_period = period_label or months[0]
    if latest_period in months:
        pivot_index = months.index(latest_period)
        months = months[pivot_index:]

    limit = {
        "this_month": 1,
        "last_3_months": 3,
        "last_12_months": 12,
    }.get(time_range, 1)
    return months[:limit]


def _collect_departments(
    db: Session,
    snapshot_id: str | None = None,
) -> list[DepartmentExportRow]:
    snapshot_id = snapshot_id or get_snapshot_id_from_aggregates(db) or ""
    dept_list = get_departments_list(db, snapshot_id=snapshot_id)
    department_ids = get_department_map(db, snapshot_id=snapshot_id)
    return [
        DepartmentExportRow(
            rank=i + 1,
            department_name=d.name,
            total_spend=d.total_spend,
            payroll_spend=d.payroll_spend,
            claims_spend=d.claims_spend,
            change_pct=d.change_pct,
        )
        for i, d in enumerate(dept_list)
        if d.id in department_ids
    ]


def _collect_anomalies(
    db: Session,
    snapshot_id: str,
    period_label: str,
    time_range: str,
) -> list[AnomalyExportRow]:
    anomaly_items = get_anomalies_list(db, snapshot_id=snapshot_id)
    months = set(_allowed_months(db, snapshot_id, period_label, time_range))
    return [
        AnomalyExportRow(
            department_name=a.get("department_name", ""),
            period=a.get("period", ""),
            description=a.get("description", ""),
            severity=a.get("severity", "low"),
            change_pct=a.get("change_pct", 0.0),
        )
        for a in anomaly_items
        if (not months or a.get("period") in months)
    ]


def _collect_trends(
    db: Session,
    snapshot_id: str | None = None,
    period_label: str = "",
    time_range: str = "all",
) -> list[MonthlyTrendExportRow]:
    snapshot_id = snapshot_id or get_snapshot_id_from_aggregates(db) or ""
    allowed_months = set(_allowed_months(db, snapshot_id, period_label, time_range))
    spends = get_all_monthly_spends(db, snapshot_id=snapshot_id)
    month_totals: dict[str, dict[str, float]] = {}
    for spend in spends:
        if allowed_months and spend.month not in allowed_months:
            continue
        if spend.month not in month_totals:
            month_totals[spend.month] = {"payroll": 0.0, "claims": 0.0}
        month_totals[spend.month]["payroll"] += spend.payroll_total
        month_totals[spend.month]["claims"] += spend.claims_total

    return [
        MonthlyTrendExportRow(
            month=month,
            payroll=round(values["payroll"], 2),
            claims=round(values["claims"], 2),
            total=round(values["payroll"] + values["claims"], 2),
        )
        for month, values in sorted(month_totals.items())
    ]


def build_payload(
    db: Session,
    snapshot_id: str | None = None,
    time_range: str = "this_month",
    include_departments: bool = True,
    include_anomalies: bool = True,
) -> ExportPayload:
    snapshot_context = _get_snapshot_context(db, snapshot_id)
    snapshot_id = (
        snapshot_context.snapshot_id if snapshot_context is not None else get_snapshot_id_from_aggregates(db) or ""
    )
    if snapshot_context is None:
        snapshot_context = SnapshotContext(
            snapshot_id=snapshot_id,
            period_label="",
            total_payroll=0.0,
            total_claims=0.0,
            department_count=0,
            anomaly_count=0,
            created_at="",
        )

    departments = _collect_departments(db, snapshot_id=snapshot_id) if include_departments else []
    anomalies = (
        _collect_anomalies(
            db,
            snapshot_id=snapshot_id,
            period_label=snapshot_context.period_label,
            time_range=time_range,
        )
        if include_anomalies
        else []
    )
    trends = _collect_trends(
        db,
        snapshot_id=snapshot_id,
        period_label=snapshot_context.period_label,
        time_range="all",
    )

    return ExportPayload(
        snapshot_id=snapshot_id,
        generated_at=iso_now(),
        departments=departments,
        anomalies=anomalies,
        summary_payroll=snapshot_context.total_payroll,
        summary_claims=snapshot_context.total_claims,
        department_count=snapshot_context.department_count,
        anomaly_count=snapshot_context.anomaly_count,
        period_label=snapshot_context.period_label,
        trends=trends,
    )
