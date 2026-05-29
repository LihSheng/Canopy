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
class SemanticMapping:
    id: str
    tenant_id: str
    dataset_id: str
    dataset_version_id: str
    version_number: int
    object_type_id: str
    object_type_key: str
    properties: list[PropertyMapping]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


@dataclass
class SchemaColumn:
    column_name: str
    primitive_type: str
