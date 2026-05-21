import os
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from common.clock import utcnow
from common.config import settings
from common.database import session_factory
from common.executor import background
from exports.builders.workbook import build_workbook
from exports.domain import ExportJob
from exports.payload import _get_snapshot_context, build_payload
from exports.presets import resolve_export_preset
from exports.repository import ExportRepository


def _default_export_dir() -> str:
    if settings.export_storage_dir:
        return settings.export_storage_dir

    if os.name == "nt":
        app_data_dir = os.environ.get("LOCALAPPDATA")
        if app_data_dir:
            return str(Path(app_data_dir) / "Canopy Intelligence" / "exports")

    return str(Path.home() / ".herd-aggregator" / "exports")


EXPORT_DIR = _default_export_dir()


def generate_export(
    db: Session,
    snapshot_id: str | None = None,
    time_range: str = "this_month",
    include_departments: bool = True,
    include_anomalies: bool = True,
) -> bytes:
    payload = build_payload(
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

    background.run(
        target=_run_export,
        args=(job_id,),
        name=f"export-{job_id}",
    )

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



