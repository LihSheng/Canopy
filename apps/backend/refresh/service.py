from datetime import UTC, datetime

from api.schemas.refresh import RefreshJobResponse, RefreshRequestResponse, RefreshStatusResponse

_last_status = RefreshStatusResponse(
    status="completed",
    last_refresh="2026-05-15T10:30:00Z",
    last_attempt="2026-05-15T10:29:00Z",
    error_message=None,
)


def trigger_refresh(user_id: str | None = None) -> RefreshRequestResponse:
    return RefreshRequestResponse(accepted=True, job_id="job-001")


def get_current_status() -> RefreshStatusResponse:
    return _last_status


def get_job(job_id: str) -> RefreshJobResponse | None:
    return RefreshJobResponse(
        job_id=job_id,
        trigger_type="manual",
        status="completed",
        requested_by_user_id="test-user-1",
        started_at=datetime(2026, 5, 15, 10, 29, 0, tzinfo=UTC),
        finished_at=datetime(2026, 5, 15, 10, 30, 0, tzinfo=UTC),
        error_message=None,
        produced_snapshot_id="snap-2026-05-15-001",
    )
