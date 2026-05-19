from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ConnectionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    SOFT_DELETED = "soft_deleted"
    DELETED = "deleted"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class Connection:
    id: str
    project_id: str
    source_type: str
    name: str
    status: str = ConnectionStatus.ACTIVE.value
    config_json: dict = field(default_factory=dict)
    test_status: str | None = None
    last_tested_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
