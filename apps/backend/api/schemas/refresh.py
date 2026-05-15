from datetime import datetime

from pydantic import BaseModel


class RefreshRequestResponse(BaseModel):
    accepted: bool
    job_id: str | None = None


class RefreshStatusResponse(BaseModel):
    status: str
    last_refresh: str | None = None
    last_attempt: str | None = None
    error_message: str | None = None


class RefreshJobResponse(BaseModel):
    job_id: str
    trigger_type: str
    status: str
    requested_by_user_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    produced_snapshot_id: str | None = None
