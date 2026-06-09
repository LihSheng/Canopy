"""Entity deprecation service — marks entities as deprecated for historical audit."""

from datetime import UTC, datetime

from common.errors import NotFoundError
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository


class EntityDeprecationService:
    """Handles deprecation of entities while preserving their published revisions."""

    def __init__(self, object_type_repo: ObjectTypeRepository):
        self._object_type_repo = object_type_repo

    def deprecate_entity(self, entity_id: str, tenant_id: str) -> ObjectType:
        """Mark an entity as deprecated.

        Deprecated entities remain visible in historical/list views but
        are hidden from normal creation flows. Published revisions stay intact.
        """
        entity = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if entity is None:
            raise NotFoundError("Entity not found")

        entity.status = "deprecated"
        entity.updated_at = datetime.now(UTC)
        return self._object_type_repo.save(entity)
