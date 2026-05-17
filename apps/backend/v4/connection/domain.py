from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ConnectionStatus(StrEnum):
    ACTIVE = "active"
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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
