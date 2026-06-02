from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SemanticType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"


class Cardinality(StrEnum):
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class CompositionKind(StrEnum):
    CONCAT = "concat"
    TEMPLATE = "template"
    LOOKUP = "lookup"


@dataclass
class FieldRef:
    """Reference to a source field from a registered source node."""

    source_id: str
    source_name: str
    field_name: str


@dataclass
class ComputedProperty:
    """A derived Entity property composed from multiple source fields.

    This is config-only; no runtime execution engine yet.
    """

    id: str
    property_name: str
    semantic_type: str = "string"
    composition_kind: str = "concat"  # concat, template, lookup
    expression: str = ""  # composition expression (e.g. "{first} {last}", "join(', ', ...)" for concat)
    inputs: list[FieldRef] = field(default_factory=list)
    included: bool = True


@dataclass
class ObjectType:
    id: str
    tenant_id: str
    object_type_key: str
    display_name: str
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


@dataclass
class PropertyMapping:
    source_column: str
    property_name: str
    semantic_type: str = "string"
    included: bool = True
    is_primary_key: bool = False


@dataclass
class EntityLink:
    link_id: str
    display_name: str
    source_property_key: str
    target_object_type_id: str
    target_property_key: str
    cardinality: str = "many_to_one"


@dataclass
class SourceNode:
    source_id: str
    source_type: str  # "dataset_table" | "static_file"
    name: str
    reference_id: str
    fields: list[str] = field(default_factory=list)


@dataclass
class SemanticMapping:
    id: str
    tenant_id: str
    dataset_id: str
    dataset_version_id: str
    version_number: int
    object_type_id: str
    object_type_key: str
    properties: list[PropertyMapping]
    links: list[EntityLink] = field(default_factory=list)
    source_nodes: list[SourceNode] = field(default_factory=list)
    computed_properties: list[ComputedProperty] = field(default_factory=list)
    layout_state: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


@dataclass
class SchemaColumn:
    column_name: str
    primitive_type: str
