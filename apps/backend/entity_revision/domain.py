"""Entity Revision domain model.

Models the lifecycle of an Entity through revisions:
- Each Entity has zero or one active draft and exactly one active published revision.
- Drafts are forked from the current published revision.
- Publishing validates all required properties and pins source dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RevisionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LinkCardinality(StrEnum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:M"


@dataclass
class EntityLink:
    """A direct link from one entity to another, with cardinality and optionality.

    link_id: Immutable UUID for the link.
    display_name: User-visible label.
    source_property_key: Property key on the source entity that holds the link value.
    target_entity_id: UUID of the target entity.
    target_property_key: Property key on the target entity to match against.
    cardinality: "1:1" or "1:M" (Phase 8 only).
    is_optional: If True, the link may resolve to None; if False, the target must exist.
    is_active: Soft-delete flag.
    """

    link_id: str
    display_name: str
    source_property_key: str
    target_entity_id: str
    target_property_key: str
    cardinality: str
    is_optional: bool = False
    is_active: bool = True

    def to_dict(self) -> dict:
        return {
            "link_id": self.link_id,
            "display_name": self.display_name,
            "source_property_key": self.source_property_key,
            "target_entity_id": self.target_entity_id,
            "target_property_key": self.target_property_key,
            "cardinality": self.cardinality,
            "is_optional": self.is_optional,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, d: dict) -> EntityLink:
        return cls(
            link_id=d.get("link_id", ""),
            display_name=d.get("display_name", ""),
            source_property_key=d.get("source_property_key", ""),
            target_entity_id=d.get("target_entity_id") or d.get("target_object_type_id", ""),
            target_property_key=d.get("target_property_key", ""),
            cardinality=d.get("cardinality", "1:1"),
            is_optional=d.get("is_optional", False),
            is_active=d.get("is_active", True),
        )


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
    is_active: bool = True  # False = planned binding (not yet active)


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
    planned_bindings: list[SourceBinding] = field(default_factory=list)
    links: list[EntityLink] = field(default_factory=list)
    source_nodes: list[dict] = field(default_factory=list)
    computed_properties: list[ComputedProperty] = field(default_factory=list)
    layout_state: dict = field(default_factory=dict)
    lock_holder_id: str | None = None
    locked_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    published_at: datetime | None = None


@dataclass
class ComputedProperty:
    """A derived Entity property composed from a formula.

    id is a stable UUID.
    property_key is the stable semantic key (e.g., 'total_comp').
    display_name is the user-visible label.
    formula is the expression string (e.g., 'salary * 1.1').
    formula_type is the category (e.g., 'arithmetic', 'concat', 'lookup').
    inputs is a list of property_key strings referenced by the formula.
    output_type is the semantic type of the result.
    """

    id: str
    property_key: str
    display_name: str
    formula: str = ""
    formula_type: str = "arithmetic"
    inputs: list[str] = field(default_factory=list)
    output_type: str = "string"
    sort_order: int = 0
    is_active: bool = True


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
