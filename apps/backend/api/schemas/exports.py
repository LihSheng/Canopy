from pydantic import BaseModel


class TriggerExportRequest(BaseModel):
    preset_name: str = "executive_summary"
    time_range: str = "this_month"
    include_departments: bool | None = None
    include_anomalies: bool | None = None


class ExportJobResponse(BaseModel):
    id: str
    status: str
    preset_name: str
    snapshot_id: str | None = None
    time_range: str = "this_month"
    snapshot_timestamp: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None


class ExportTriggerResponse(BaseModel):
    accepted: bool
    job_id: str


class ExportHistoryResponse(BaseModel):
    jobs: list[ExportJobResponse]


class RerunExportRequest(BaseModel):
    pass
