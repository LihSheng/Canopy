from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Project:
    id: str
    tenant_id: str | None = None
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
