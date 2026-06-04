"""Entity lineage graph domain model.

Defines the generic lineage graph contract for Entity Manager:
- Node kinds: dataset, source, derived, entity
- Edge kinds: lineage, binding, link

The Entity is the central node. Dataset and Dataset Version appear as upstream
context. Source nodes feed into the Dataset Version. Source-field-to-property
bindings are binding edges. Entity-to-Entity relationships are link edges.
Derived nodes can appear along lineage paths when stored.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class LineageNodeKind(StrEnum):
    DATASET = "dataset"
    SOURCE = "source"
    DERIVED = "derived"
    ENTITY = "entity"


class LineageEdgeKind(StrEnum):
    LINEAGE = "lineage"
    BINDING = "binding"
    LINK = "link"


@dataclass
class LineageNode:
    """A node in the entity-centric lineage graph."""

    id: str
    kind: LineageNodeKind
    label: str
    properties: list[str] = field(default_factory=list)
    collapsed: bool = False
    collapsed_count: int = 0
    subtype: str = ""


@dataclass
class LineageEdge:
    """An edge in the entity-centric lineage graph."""

    id: str
    kind: LineageEdgeKind
    source_id: str
    target_id: str
    label: str = ""
    source_handle: str = ""
    target_handle: str = ""


@dataclass
class EntityLineageGraph:
    """The complete entity-centered lineage graph read model.

    Built from entity revision data, dataset/version context, and
    source node bindings.  Supports derived nodes when present.
    """

    entity_id: str
    entity_label: str
    nodes: list[LineageNode] = field(default_factory=list)
    edges: list[LineageEdge] = field(default_factory=list)
    layout_state: dict = field(default_factory=dict)
