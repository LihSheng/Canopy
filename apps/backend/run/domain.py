from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Run:
    id: str
    connection_id: str
    dataset_id: str
    project_id: str = ""
    tenant_id: str | None = None
    status: str = RunStatus.QUEUED.value
    started_by: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int = 0
    warning_count: int = 0
    error_message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
