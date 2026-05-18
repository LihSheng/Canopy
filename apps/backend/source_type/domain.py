from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SourceTypeCategory(StrEnum):
    FILE = "file"
    DATABASE = "database"
    API = "api"
    OTHER = "other"


@dataclass
class SourceType:
    id: str
    key: str
    label: str
    category: str = SourceTypeCategory.OTHER.value
    enabled: bool = False
    tags: list[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None
