import os
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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
from common.clock import iso_now, utcnow
from common.config import settings
from common.database import session_factory
from exports.builders.workbook import build_workbook
from exports.domain import (
    AnomalyExportRow,
    DepartmentExportRow,
    ExportJob,
    ExportPayload,
    MonthlyTrendExportRow,
)
from exports.presets import resolve_export_preset
from exports.repository import ExportRepository


@dataclass(frozen=True)
class SnapshotContext:
    snapshot_id: str
    period_label: str
    total_payroll: float
    total_claims: float
    department_count: int
    anomaly_count: int
    created_at: str


def _default_export_dir() -> str:
    if settings.export_storage_dir:
        return settings.export_storage_dir

    if os.name == "nt":
        app_data_dir = os.environ.get("LOCALAPPDATA")
        if app_data_dir:
            return str(Path(app_data_dir) / "HERD Aggregator" / "exports")

    return str(Path.home() / ".herd-aggregator" / "exports")


EXPORT_DIR = _default_export_dir()


def generate_export(
    db: Session,
    snapshot_id: str | None = None,
    time_range: str = "this_month",
    include_departments: bool = True,
    include_anomalies: bool = True,
) -> bytes:
    payload = _build_payload(
        db=db,
        snapshot_id=snapshot_id,
        time_range=time_range,
        include_departments=include_departments,
        include_anomalies=include_anomalies,
    )
    return build_workbook(payload)


def trigger_export(
    preset_name: str,
    time_range: str,
    user_id: str | None = None,
    include_departments: bool | None = None,
    include_anomalies: bool | None = None,
) -> ExportJob:
    preset = resolve_export_preset(preset_name)
    snapshot_context = _get_snapshot_context()
    job_id = str(uuid.uuid4())
    job = ExportJob(
        id=job_id,
        status="pending",
        preset_name=preset.label,
        snapshot_id=snapshot_context.snapshot_id if snapshot_context else None,
        time_range=time_range,
        snapshot_timestamp=snapshot_context.created_at if snapshot_context else None,
        requested_by_user_id=user_id,
        include_departments=include_departments,
        include_anomalies=include_anomalies,
    )
    job.include_departments = (
        include_departments
        if include_departments is not None
        else preset.include_departments
    )
    job.include_anomalies = (
        include_anomalies
        if include_anomalies is not None
        else preset.include_anomalies
    )

    db = session_factory()()
    try:
        repo = ExportRepository(db)
        repo.save_job(job)
    finally:
        db.close()

    thread = threading.Thread(
        target=_run_export,
        args=(job_id,),
        daemon=True,
        name=f"export-{job_id}",
    )
    thread.start()

    return job


def get_export_job(job_id: str) -> ExportJob | None:
    db = session_factory()()
    try:
        repo = ExportRepository(db)
        model = repo.get_job(job_id)
        if model is None:
            return None
        return _model_to_domain(model)
    finally:
        db.close()


def get_export_history(limit: int = 20) -> list[ExportJob]:
    db = session_factory()()
    try:
        repo = ExportRepository(db)
        models = repo.get_recent_jobs(limit)
        return [_model_to_domain(m) for m in models]
    finally:
        db.close()


def rerun_export(export_id: str) -> ExportJob | None:
    existing = get_export_job(export_id)
    if existing is None:
        return None
    return trigger_export(
        preset_name=existing.preset_name,
        time_range=existing.time_range,
        user_id=existing.requested_by_user_id,
        include_departments=existing.include_departments,
        include_anomalies=existing.include_anomalies,
    )


def _run_export(job_id: str) -> None:
    db = session_factory()()
    try:
        repo = ExportRepository(db)
        model = repo.get_job(job_id)
        if model is None:
            return

        model.status = "running"
        model.started_at = utcnow()
        db.commit()

        excel_bytes = generate_export(
            db=db,
            snapshot_id=model.snapshot_id,
            time_range=model.time_range,
            include_departments=model.include_departments,
            include_anomalies=model.include_anomalies,
        )
        snapshot_context = _get_snapshot_context(db, model.snapshot_id)

        job = _model_to_domain(model)
        job.status = "completed"
        if snapshot_context is not None:
            job.snapshot_id = snapshot_context.snapshot_id
            job.snapshot_timestamp = snapshot_context.created_at
        job.finished_at = utcnow()
        job.file_size_bytes = len(excel_bytes)

        os.makedirs(EXPORT_DIR, exist_ok=True)
        file_path = os.path.join(EXPORT_DIR, f"{job_id}.xlsx")
        with open(file_path, "wb") as f:
            f.write(excel_bytes)
        job.file_path = file_path

        repo.update_job(job)
    except Exception as exc:
        job = _model_to_domain(model) if model else ExportJob(id=job_id)
        job.status = "failed"
        job.finished_at = utcnow()
        job.error_message = str(exc)
        repo.update_job(job)
    finally:
        db.close()


def _get_snapshot_id(db: Session) -> str | None:
    try:
        return get_snapshot_id_from_aggregates(db)
    except Exception:
        return None


def _get_snapshot_context(
    db: Session | None = None,
    snapshot_id: str | None = None,
) -> SnapshotContext | None:
    owns_db = db is None
    db = db or session_factory()()
    try:
        summary = (
            get_summary_cache_for_snapshot(db, snapshot_id)
            if snapshot_id
            else get_dashboard_summary(db)
        )
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


def _model_to_domain(model) -> ExportJob:
    return ExportJob(
        id=model.id,
        status=model.status,
        preset_name=model.preset_name,
        snapshot_id=model.snapshot_id,
        time_range=model.time_range,
        snapshot_timestamp=model.snapshot_timestamp,
        requested_by_user_id=model.requested_by_user_id,
        include_departments=model.include_departments,
        include_anomalies=model.include_anomalies,
        file_path=model.file_path,
        file_size_bytes=model.file_size_bytes,
        started_at=model.started_at,
        finished_at=model.finished_at,
        error_message=model.error_message,
    )


def _build_payload(
    db: Session,
    snapshot_id: str | None = None,
    time_range: str = "this_month",
    include_departments: bool = True,
    include_anomalies: bool = True,
) -> ExportPayload:
    snapshot_context = _get_snapshot_context(db, snapshot_id)
    snapshot_id = (
        snapshot_context.snapshot_id
        if snapshot_context is not None
        else get_snapshot_id_from_aggregates(db) or ""
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

    departments = (
        _collect_departments(db, snapshot_id=snapshot_id) if include_departments else []
    )
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
