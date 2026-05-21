import uuid
from datetime import UTC, datetime

from source_type.domain import SourceType, SourceTypeCategory
from source_type.repository import SourceTypeRepository

_SEED_TYPES = [
    {
        "key": "static_file",
        "label": "Static File",
        "category": SourceTypeCategory.FILE.value,
        "enabled": True,
        "tags": ["file"],
        "description": "Upload a static file (CSV, Excel, JSON, Parquet)",
    },
    {
        "key": "mysql",
        "label": "MySQL",
        "category": SourceTypeCategory.DATABASE.value,
        "enabled": True,
        "tags": ["database", "sql"],
        "description": "MySQL database connection",
    },
    {
        "key": "postgresql",
        "label": "PostgreSQL",
        "category": SourceTypeCategory.DATABASE.value,
        "enabled": True,
        "tags": ["database", "sql"],
        "description": "PostgreSQL database connection",
    },
    {
        "key": "rest_api",
        "label": "REST API",
        "category": SourceTypeCategory.API.value,
        "enabled": False,
        "tags": ["api", "http"],
        "description": "REST API endpoint",
    },
    {
        "key": "google_sheets",
        "label": "Google Sheets",
        "category": SourceTypeCategory.API.value,
        "enabled": False,
        "tags": ["api", "sheets"],
        "description": "Google Sheets integration",
    },
    {
        "key": "csv",
        "label": "CSV File",
        "category": SourceTypeCategory.FILE.value,
        "enabled": False,
        "tags": ["file", "csv"],
        "description": "CSV file upload",
    },
]


class SourceTypeService:
    def __init__(self, repo: SourceTypeRepository):
        self._repo = repo

    def ensure_seeded(self) -> None:
        existing = self._repo.list_all()
        existing_keys = {st.key for st in existing}
        now = datetime.now(UTC)
        for entry in _SEED_TYPES:
            if entry["key"] not in existing_keys:
                st = SourceType(
                    id=str(uuid.uuid4()),
                    key=entry["key"],
                    label=entry["label"],
                    category=entry["category"],
                    enabled=entry["enabled"],
                    tags=entry["tags"],
                    description=entry["description"],
                    created_at=now,
                )
                self._repo.save(st)

    def list_source_types(self) -> list[SourceType]:
        return self._repo.list_all()

    def get_enabled(self) -> list[SourceType]:
        return self._repo.get_enabled()
