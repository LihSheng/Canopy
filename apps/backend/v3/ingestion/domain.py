from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class UploadStatus(StrEnum):
    uploaded = "uploaded"
    profiled = "profiled"
    failed = "failed"


class CleaningStepType(StrEnum):
    trim = "trim"
    rename = "rename"
    cast = "cast"
    parse_date = "parse_date"
    dedupe = "dedupe"
    normalize_nulls = "normalize_nulls"
    filter_empty_rows = "filter_empty_rows"


class PipelineStatus(StrEnum):
    draft = "draft"
    published = "published"


class TemplateFamilyStatus(StrEnum):
    active = "active"
    archived = "archived"


class TemplateVersionState(StrEnum):
    draft = "draft"
    published = "published"


class CleanedSnapshotStatus(StrEnum):
    completed = "completed"
    completed_with_warnings = "completed_with_warnings"
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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SheetProfile:
    upload_id: str | None = None
    sheet_name: str = ""
    row_count: int = 0
    data_row_count: int = 0
    column_count: int = 0
    header_row_index: int | None = None
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    preview_columns: list[str] = field(default_factory=list)
    preview_rows: list[list[object | None]] = field(default_factory=list)
    is_visible: bool = True
    merged_cell_ranges: list[str] = field(default_factory=list)
    contains_formulas: bool = False
    raw_cells: list[list[object | None]] | None = None


@dataclass
class ColumnProfile:
    column_name: str = ""
    detected_type: str = "text"
    non_null_count: int = 0
    sample_values: list[object] = field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class MappingDecision:
    source_column_name: str
    target_field_name: str
    confirmed: bool
    overridden_by_user: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkbookProfile:
    sheets: list[SheetProfile] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class CleaningStep:
    id: str
    step_type: str
    order: int
    parameters: dict = field(default_factory=dict)
    description: str | None = None


@dataclass
class TemplateFamily:
    id: str
    dataset_type: str
    source_profile: str
    name: str
    description: str
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TemplateVersion:
    id: str
    template_id: str
    version_number: int
    state: str
    spec_json: dict
    published_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CleaningPipeline:
    id: str
    upload_id: str
    steps: list[CleaningStep]
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CleaningResult:
    rows: list[dict]
    warnings: list[str] = field(default_factory=list)
    rename_map: dict[str, str] = field(default_factory=dict)
    row_count: int = 0
    status: str = "completed"


@dataclass
class NormalizedOutput:
    rows: list[dict]
    field_map: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CleanedSnapshot:
    id: str
    upload_id: str
    template_version_id: str
    status: str
    row_count: int
    warning_count: int
    warnings: list[str]
    storage_path: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class LineageNodeType(StrEnum):
    file = "file"
    workbook = "workbook"
    sheet = "sheet"
    raw_column = "raw_column"
    cleaned_field = "cleaned_field"
    ontology_field = "ontology_field"


class LineageEdgeType(StrEnum):
    derived_from = "derived_from"
    mapped_to = "mapped_to"
    normalized_to = "normalized_to"


@dataclass
class LineageNode:
    id: str
    node_type: LineageNodeType
    label: str
    metadata: dict = field(default_factory=dict)


@dataclass
class LineageEdge:
    id: str
    from_node_id: str
    to_node_id: str
    edge_type: LineageEdgeType
    metadata: dict = field(default_factory=dict)


@dataclass
class LineageGraph:
    nodes: list[LineageNode] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)


@dataclass
class LineageRecord:
    upload_id: str
    snapshot_id: str
    graph: LineageGraph
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class IngestionWorkflowStatus(StrEnum):
    started = "started"
    profiled = "profiled"
    mapped = "mapped"
    processing = "processing"
    processed = "processed"
    published = "published"
    failed = "failed"


@dataclass
class WorkflowState:
    upload_id: str
    status: IngestionWorkflowStatus
    error_message: str | None = None
    cleaned_snapshot_id: str | None = None
    publish_id: str | None = None
    completed_steps: list[str] = field(default_factory=list)
    current_step: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class PublishStatus(StrEnum):
    pending = "pending"
    active = "active"
    revoked = "revoked"


@dataclass
class PublishValidationResult:
    valid: bool
    warnings: list[str]
    errors: list[str]


@dataclass
class PublishRecord:
    id: str
    upload_id: str
    cleaned_snapshot_id: str
    template_version_id: str
    status: str
    validation_errors: list[str]
    validation_warnings: list[str]
    published_at: datetime | None = None
    published_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
