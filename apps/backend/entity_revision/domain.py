"""Entity Revision domain model.

Models the lifecycle of an Entity through revisions:
- Each Entity has zero or one active draft and exactly one active published revision.
- Drafts are forked from the current published revision.
- Publishing validates all required properties and pins source dependencies.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RevisionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class EntityProperty:
    """A canonical, business-owned property definition with stable identity.

    property_id is an immutable UUID that survives renames.
    property_key is the stable semantic key (e.g., 'employee_name').
    display_name is the user-visible label (e.g., 'Employee Name').
    """

    property_id: str
    property_key: str
    display_name: str
    semantic_type: str = "string"
    is_required: bool = False
    is_primary_key: bool = False
    sort_order: int = 0


@dataclass
class SourceBinding:
    """A binding from a source field to an entity property.

    Maps a source_node.field_name -> entity PropertyMapping (via property_key).
    """

    property_key: str
    source_node_id: str
    source_field_name: str
    source_column: str = ""  # Deprecated alias; retained for backward compat


@dataclass
class EntityRevision:
    """A snapshot of an Entity's semantic configuration at a point in time.

    Each revision stores the full entity config: properties, bindings, links,
    source nodes, and computed properties. Exactly one revision per entity
    can be 'published' at a time; at most one can be 'draft'.
    """

    id: str
    entity_id: str
    revision_number: int
    status: str  # RevisionStatus value
    forked_from_revision_id: str | None = None
    properties: list[EntityProperty] = field(default_factory=list)
    source_bindings: list[SourceBinding] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    source_nodes: list[dict] = field(default_factory=list)
    computed_properties: list[dict] = field(default_factory=list)
    layout_state: dict = field(default_factory=dict)
    lock_holder_id: str | None = None
    locked_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None


@dataclass
class EntityRevisionDependency:
    """A pinned source dependency for a published entity revision.

    Tracks which datasets and dataset versions a published revision depends on,
    enabling delete protection and reproducibility.
    """

    id: str
    revision_id: str
    dependency_type: str  # "dataset" | "dataset_version"
    dependency_id: str
