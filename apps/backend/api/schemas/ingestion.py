from datetime import datetime

from pydantic import BaseModel


class UploadRequest(BaseModel):
    file_name: str
    source_profile: str
    dataset_type: str


class UploadResponse(BaseModel):
    upload_id: str
    status: str
    file_name: str
    file_size: int
    checksum: str
    created_at: datetime


class ColumnProfileResponse(BaseModel):
    source_column_name: str
    inferred_type: str
    sample_values: list[str]
    null_ratio: float
    confidence: float
    suggested_target_field: str | None = None


class SheetProfileResponse(BaseModel):
    sheet_name: str
    row_count: int
    column_count: int
    header_row_index: int | None
    confidence: float
    warnings: list[str]


class MappingDecisionRequest(BaseModel):
    source_column_name: str
    target_field_name: str
    confirmed: bool
    overridden_by_user: bool


class MappingDecisionResponse(BaseModel):
    source_column_name: str
    target_field_name: str
    confirmed: bool
    overridden_by_user: bool


class MappingSuggestionsResponse(BaseModel):
    upload_id: str
    decisions: list[MappingDecisionResponse]
    column_profiles: list[ColumnProfileResponse]


class WorkbookProfileResponse(BaseModel):
    upload_id: str
    best_sheet_name: str | None
    sheet_profiles: list[SheetProfileResponse]
    column_profiles: list[ColumnProfileResponse]
    preview_rows: list[list[str | None]]
    warnings: list[str]
