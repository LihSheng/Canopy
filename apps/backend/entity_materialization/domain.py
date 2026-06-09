"""Entity materialization domain models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EntityMaterializedRow:
    """A single materialized row for an entity revision.

    Represents the runtime view of an entity instance, produced by
    reading source data and applying source bindings.
    """

    id: str
    entity_id: str
    revision_id: str
    row_id: str
    row_data: dict
    is_tombstone: bool = False
    materialized_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
