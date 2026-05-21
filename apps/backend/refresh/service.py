import uuid

from api.schemas.refresh import RefreshJobResponse, RefreshRequestResponse, RefreshStatusResponse
from common.database import session_factory
from common.executor import background
from refresh.domain import RefreshJob
from refresh.orchestration.service import RefreshOrchestrator
from refresh.repository import RefreshRepository
from sync.source_db import source_session_factory


def trigger_refresh(user_id: str | None = None) -> RefreshRequestResponse:
    job_id = str(uuid.uuid4())
    job = RefreshJob(
        id=job_id,
        status="pending",
        trigger_type="manual",
        requested_by_user_id=user_id,
    )

    db = session_factory()()
    try:
        repo = RefreshRepository(db)
        repo.save_job(job)
    finally:
        db.close()

    background.run(
        target=_run_refresh,
        args=(job_id,),
        name=f"refresh-{job_id}",
    )

    return RefreshRequestResponse(accepted=True, job_id=job_id)


def get_current_status() -> RefreshStatusResponse:
    db = session_factory()()
    try:
        repo = RefreshRepository(db)
        latest = repo.get_latest_job()

        if latest is None:
            return RefreshStatusResponse(
                status="idle",
                last_refresh=None,
                last_attempt=None,
                error_message=None,
            )

        last_refresh = None
        last_attempt = latest.started_at.isoformat() if latest.started_at else None

        if latest.status == "completed" and latest.finished_at:
            last_refresh = latest.finished_at.isoformat()

        return RefreshStatusResponse(
            status=latest.status,
            last_refresh=last_refresh,
            last_attempt=last_attempt,
            error_message=latest.error_message,
        )
    finally:
        db.close()


def get_job(job_id: str) -> RefreshJobResponse | None:
    db = session_factory()()
    try:
        repo = RefreshRepository(db)
        model = repo.get_job(job_id)
        if model is None:
            return None

        return RefreshJobResponse(
            job_id=model.id,
            trigger_type=model.trigger_type,
            status=model.status,
            requested_by_user_id=model.requested_by_user_id,
            started_at=model.started_at,
            finished_at=model.finished_at,
            error_message=model.error_message,
            produced_snapshot_id=model.snapshot_id,
        )
    finally:
        db.close()


def _run_refresh(job_id: str) -> None:
    db = session_factory()()
    source_db = source_session_factory()()
    try:
        repo = RefreshRepository(db)
        job_model = repo.get_job(job_id)
        if job_model is None:
            return
        job = _model_to_domain(job_model)

        orchestrator = RefreshOrchestrator(app_db=db, source_db=source_db)
        orchestrator.run(job)
    finally:
        db.close()
        source_db.close()


def _model_to_domain(model) -> RefreshJob:
    return RefreshJob(
        id=model.id,
        status=model.status,
        current_stage=model.current_stage,
        snapshot_id=model.snapshot_id,
        trigger_type=model.trigger_type,
        requested_by_user_id=model.requested_by_user_id,
        started_at=model.started_at,
        finished_at=model.finished_at,
        error_message=model.error_message,
    )
