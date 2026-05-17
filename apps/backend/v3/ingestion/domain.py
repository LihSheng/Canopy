from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class CleaningStep:
    id: str
    step_type: str
    order: int
    parameters: dict
    description: str | None = None


@dataclass
class TemplateFamily:
    id: str
    dataset_type: str
    source_profile: str
    name: str
    description: str
    status: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TemplateVersion:
    id: str
    template_id: str
    version_number: int
    state: str
    spec_json: dict
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: datetime | None = None


@dataclass
class CleaningPipeline:
    id: str
    upload_id: str
    steps: list[CleaningStep]
    status: str
    template_version_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CleaningResult:
    rows: list[dict]
    warnings: list[str]
    row_count: int
    status: str
    rename_map: dict[str, str] = field(default_factory=dict)


@dataclass
class NormalizedOutput:
    rows: list[dict]
    field_map: dict[str, str]
    warnings: list[str]


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
    created_at: datetime = field(default_factory=datetime.now)


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
    created_at: datetime = field(default_factory=datetime.now)

