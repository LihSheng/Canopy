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


class TemplateFamilyRequest(BaseModel):
    dataset_type: str
    source_profile: str
    name: str
    description: str = ""


class TemplateFamilyResponse(BaseModel):
    id: str
    dataset_type: str
    source_profile: str
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class TemplateVersionResponse(BaseModel):
    id: str
    template_id: str
    version_number: int
    state: str
    spec_json: dict
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None


class TemplateFamilyDetailResponse(BaseModel):
    id: str
    dataset_type: str
    source_profile: str
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    versions: list[TemplateVersionResponse]


class CreateTemplateVersionRequest(BaseModel):
    clone_from_version_id: str | None = None
    spec_json: dict = {}


class BindTemplateRequest(BaseModel):
    template_version_id: str


class TemplateVersionListResponse(BaseModel):
    template_id: str
    versions: list[TemplateVersionResponse]


class CleaningStepRequest(BaseModel):
    step_type: str
    order: int
    parameters: dict
    description: str | None = None


class CleaningStepResponse(BaseModel):
    id: str
    step_type: str
    order: int
    parameters: dict
    description: str | None = None


class CleaningPipelineResponse(BaseModel):
    id: str
    upload_id: str
    status: str
    steps: list[CleaningStepResponse]
    template_version_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CreatePipelineRequest(BaseModel):
    upload_id: str


class ReorderStepsRequest(BaseModel):
    step_ids: list[str]


class PipelineValidationResponse(BaseModel):
    warnings: list[str]


class CleanedSnapshotResponse(BaseModel):
    id: str
    upload_id: str
    template_version_id: str
    status: str
    row_count: int
    warning_count: int
    warnings: list[str]
    created_at: datetime


class ProcessUploadResponse(BaseModel):
    cleaned_snapshot_id: str
    status: str
    row_count: int
    warning_count: int
    warnings: list[str]


class LineageNodeResponse(BaseModel):
    id: str
    node_type: str
    label: str
    metadata: dict


class LineageEdgeResponse(BaseModel):
    id: str
    from_node_id: str
    to_node_id: str
    edge_type: str
    metadata: dict


class LineageGraphResponse(BaseModel):
    upload_id: str
    nodes: list[LineageNodeResponse]
    edges: list[LineageEdgeResponse]


class PublishValidationResponse(BaseModel):
    valid: bool
    warnings: list[str]
    errors: list[str]


class PublishRecordResponse(BaseModel):
    id: str
    upload_id: str
    cleaned_snapshot_id: str
    template_version_id: str
    status: str
    published_at: datetime | None = None
    published_by: str | None = None
    validation_errors: list[str]
    validation_warnings: list[str]
    created_at: datetime


class PublishHistoryResponse(BaseModel):
    records: list[PublishRecordResponse]
