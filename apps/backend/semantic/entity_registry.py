"""Entity registry read model.

Standalone read-model queries for entity listing and detail.
Separate from SemanticMappingRepository (which owns mutation) per PRD 0015 —
"Keep data access narrow and role-specific instead of creating a generic
entity service that knows everything."

These functions take a plain db session; they are not bound to a repository.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from dataset.schema import DatasetModel
from semantic.repository import SemanticMappingRepository
from semantic.schema import ObjectTypeModel, SemanticMappingModel


def list_entity_registry_items(db: Session, tenant_id: str, search: str | None = None) -> list[dict]:
    """Return a flat read model of all entities (object types + latest mapping).

    Each row includes object_type info, latest mapping summary, and backing
    dataset name.  The result is a list of dicts suitable for direct
    serialisation to an API response.
    """

    # Subquery: latest mapping version per object_type_id within the tenant
    latest_sub = (
        db.query(
            SemanticMappingModel.object_type_id,
            func.max(SemanticMappingModel.version_number).label("max_version"),
        )
        .filter(SemanticMappingModel.tenant_id == tenant_id)
        .group_by(SemanticMappingModel.object_type_id)
        .subquery()
    )

    # Full latest mapping row per object type
    latest_mappings = (
        db.query(SemanticMappingModel)
        .join(
            latest_sub,
            (SemanticMappingModel.object_type_id == latest_sub.c.object_type_id)
            & (SemanticMappingModel.version_number == latest_sub.c.max_version),
        )
        .filter(SemanticMappingModel.tenant_id == tenant_id)
        .subquery()
    )

    q = (
        db.query(
            ObjectTypeModel.id,
            ObjectTypeModel.object_type_key,
            ObjectTypeModel.display_name,
            ObjectTypeModel.description,
            ObjectTypeModel.created_at,
            ObjectTypeModel.updated_at,
            latest_mappings.c.id.label("mapping_id"),
            latest_mappings.c.dataset_id,
            latest_mappings.c.dataset_version_id,
            latest_mappings.c.version_number.label("mapping_version_number"),
            latest_mappings.c.properties,
            latest_mappings.c.links,
            latest_mappings.c.computed_properties,
            latest_mappings.c.updated_at.label("mapping_updated_at"),
            DatasetModel.name.label("dataset_name"),
        )
        .join(
            latest_mappings,
            ObjectTypeModel.id == latest_mappings.c.object_type_id,
            isouter=True,
        )
        .join(
            DatasetModel,
            latest_mappings.c.dataset_id == DatasetModel.id,
            isouter=True,
        )
        .filter(ObjectTypeModel.tenant_id == tenant_id)
    )

    if search:
        like = f"%{search}%"
        q = q.filter(
            (ObjectTypeModel.display_name.ilike(like))
            | (ObjectTypeModel.object_type_key.ilike(like))
            | (DatasetModel.name.ilike(like))
        )

    q = q.order_by(ObjectTypeModel.updated_at.desc())

    rows = q.all()
    return [row._asdict() if hasattr(row, "_asdict") else dict(row._mapping) for row in rows]


def get_entity_detail_read_model(db: Session, tenant_id: str, object_type_id: str) -> dict | None:
    """Return a full entity detail read model for a single object type.

    Includes object_type info, the latest mapping (full domain object), and
    the backing dataset name.
    """
    obj = (
        db.query(ObjectTypeModel)
        .filter(
            ObjectTypeModel.id == object_type_id,
            ObjectTypeModel.tenant_id == tenant_id,
        )
        .first()
    )
    if obj is None:
        return None

    mapping_repo = SemanticMappingRepository(db)
    latest = mapping_repo.get_latest_by_object_type_id(tenant_id, object_type_id)

    dataset_name = None
    if latest:
        ds = db.query(DatasetModel).filter(DatasetModel.id == latest.dataset_id).first()
        dataset_name = ds.name if ds else None

    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "object_type_key": obj.object_type_key,
        "display_name": obj.display_name,
        "description": obj.description,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "mapping": latest if latest else None,
        "dataset_name": dataset_name,
    }
