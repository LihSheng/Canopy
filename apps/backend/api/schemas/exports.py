from pydantic import BaseModel


class ExportRequest(BaseModel):
    include_departments: bool = True
    include_anomalies: bool = True


class ExportResponse(BaseModel):
    accepted: bool
    download_url: str | None = None
    status: str = "queued"
