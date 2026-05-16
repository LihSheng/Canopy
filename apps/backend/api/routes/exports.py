import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from io import BytesIO

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.exports import (
    ExportHistoryResponse,
    ExportJobResponse,
    ExportTriggerResponse,
    TriggerExportRequest,
)
from common.database import session_factory
from exports.service import (
    generate_export,
    get_export_history,
    get_export_job,
    rerun_export,
    trigger_export,
)

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _job_to_response(job) -> ExportJobResponse:
    return ExportJobResponse(
        id=job.id,
        status=job.status,
        preset_name=job.preset_name,
        snapshot_id=job.snapshot_id,
        time_range=job.time_range,
        snapshot_timestamp=job.snapshot_timestamp,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        file_size_bytes=job.file_size_bytes,
        error_message=job.error_message,
    )


@router.post("/trigger")
def export_trigger(
    body: TriggerExportRequest,
    current_user: SessionUser = Depends(get_current_user),
):
    job = trigger_export(
        preset_name=body.preset_name,
        time_range=body.time_range,
        user_id=current_user.id,
        include_departments=body.include_departments,
        include_anomalies=body.include_anomalies,
    )
    return ExportTriggerResponse(accepted=True, job_id=job.id)


@router.get("/history")
def export_history(
    current_user: SessionUser = Depends(get_current_user),
):
    jobs = get_export_history(limit=20)
    return ExportHistoryResponse(
        jobs=[_job_to_response(j) for j in jobs]
    )


@router.get("/jobs/{job_id}")
def export_job_status(
    job_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    job = get_export_job(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"detail": "Export job not found"})
    return _job_to_response(job)


@router.get("/jobs/{job_id}/download")
def export_job_download(
    job_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    job = get_export_job(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"detail": "Export job not found"})
    if job.status != "completed" or not job.file_path:
        return JSONResponse(status_code=400, content={"detail": "Export not ready for download"})
    if not os.path.isfile(job.file_path):
        return JSONResponse(status_code=404, content={"detail": "Export file not found"})

    safe_name = job.preset_name.replace(" ", "-").lower()
    filename = f"{safe_name}-{job.id[:8]}.xlsx"
    return FileResponse(
        job.file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@router.post("/jobs/{job_id}/rerun")
def export_rerun(
    job_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    job = rerun_export(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"detail": "Export job not found"})
    return ExportTriggerResponse(accepted=True, job_id=job.id)


@router.post("/executive-summary")
def export_executive_summary(
    body: TriggerExportRequest,
    current_user: SessionUser = Depends(get_current_user),
):
    db = session_factory()()
    try:
        excel_bytes = generate_export(
            db=db,
            include_departments=(
                True if body.include_departments is None else body.include_departments
            ),
            include_anomalies=(
                True if body.include_anomalies is None else body.include_anomalies
            ),
        )
    finally:
        db.close()

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=executive-summary.xlsx"
        },
    )
