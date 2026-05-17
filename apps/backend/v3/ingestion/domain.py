from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class UploadStatus(StrEnum):
    uploaded = "uploaded"
    profiled = "profiled"
    failed = "failed"


@dataclass
class UploadRecord:
    id: str
    file_name: str
    file_size: int
    mime_type: str
    storage_path: str
    checksum: str
    status: UploadStatus
    source_profile: str
    dataset_type: str
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SheetProfile:
    sheet_name: str
    row_count: int
    column_count: int
    header_row_index: int | None
    confidence: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class ColumnProfile:
    source_column_name: str
    inferred_type: str
    sample_values: list[str]
    null_ratio: float
    confidence: float
    suggested_target_field: str | None = None


@dataclass
class MappingDecision:
    source_column_name: str
    target_field_name: str
    confirmed: bool
    overridden_by_user: bool


@dataclass
class WorkbookProfile:
    upload_id: str
    best_sheet_name: str | None
    sheet_profiles: list[SheetProfile]
    column_profiles: list[ColumnProfile]
    preview_rows: list[list[str | None]]
    warnings: list[str] = field(default_factory=list)

