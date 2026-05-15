from datetime import datetime

from sqlalchemy.orm import Session

from analytics.departments import get_departments as get_departments_list
from analytics.domain import MonthlyDepartmentSpend
from analytics.repositories.analytics import AnalyticsRepository
from analytics.service import get_dashboard_summary, get_monthly_trends
from anomalies.repository import AnomalyRepository
from anomalies.service import get_anomalies_list
from common.clock import iso_now
from exports.builders.workbook import build_workbook
from exports.domain import (
    AnomalyExportRow,
    DepartmentExportRow,
    ExportPayload,
    MonthlyTrendExportRow,
)


def generate_export(
    db: Session,
    include_departments: bool = True,
    include_anomalies: bool = True,
) -> bytes:
    payload = _build_payload(db, include_departments, include_anomalies)
    return build_workbook(payload)


def _build_payload(
    db: Session,
    include_departments: bool,
    include_anomalies: bool,
) -> ExportPayload:
    analytics_repo = AnalyticsRepository(db)
    summary = get_dashboard_summary(db)
    snapshot_id = analytics_repo.get_snapshot_id_from_aggregates() or ""

    departments = _collect_departments(db) if include_departments else []
    anomalies = _collect_anomalies(db) if include_anomalies else []
    trends = _collect_trends(db)

    return ExportPayload(
        snapshot_id=snapshot_id,
        generated_at=iso_now(),
        departments=departments,
        anomalies=anomalies,
        summary_payroll=summary.total_payroll,
        summary_claims=summary.total_claims,
        department_count=summary.department_count,
        anomaly_count=summary.anomaly_count,
        period_label=f"{summary.period.year}-{summary.period.month:02d}",
        trends=trends,
    )


def _collect_departments(db: Session) -> list[DepartmentExportRow]:
    dept_list = get_departments_list(db)
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
    ]


def _collect_anomalies(db: Session) -> list[AnomalyExportRow]:
    anomaly_items = get_anomalies_list(db)
    return [
        AnomalyExportRow(
            department_name=a.get("department_name", ""),
            period=a.get("period", ""),
            description=a.get("description", ""),
            severity=a.get("severity", "low"),
            change_pct=a.get("change_pct", 0.0),
        )
        for a in anomaly_items
    ]


def _collect_trends(db: Session) -> list[MonthlyTrendExportRow]:
    trends = get_monthly_trends(db)
    return [
        MonthlyTrendExportRow(
            month=t.month,
            payroll=t.payroll,
            claims=t.claims,
            total=t.total,
        )
        for t in trends
    ]
