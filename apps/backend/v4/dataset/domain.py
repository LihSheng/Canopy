from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class DatasetStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class Dataset:
    id: str
    project_id: str
    connection_id: str
    name: str
    source_object_name: str = ""
    status: str = DatasetStatus.ACTIVE.value
    active_version_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


class DatasetVersionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class DatasetVersion:
    id: str
    dataset_id: str
    run_id: str | None = None
    version_number: int = 1
    status: str = DatasetVersionStatus.PENDING.value
    row_count: int = 0
    column_count: int = 0
    storage_path: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
