"""Entity registry read model.

Standalone read-model queries for entity listing and detail.
Separate from SemanticMappingRepository (which owns mutation) per PRD 0015 —
"Keep data access narrow and role-specific instead of creating a generic
entity service that knows everything."

These functions take a plain db session; they are not bound to a repository.
"""

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from dataset.schema import DatasetModel
from semantic.repository import SemanticMappingRepository
from semantic.schema import ObjectTypeModel, SemanticMappingModel


def list_entity_registry_items(
    db: Session,
    tenant_id: str,
    search: str | None = None,
    exclude_deprecated: bool = False,
) -> list[dict]:
    """Return a flat read model of all entities (object types + latest mapping).

    Each row includes object_type info, latest mapping summary, and backing
    dataset name.  The result is a list of dicts suitable for direct
    serialisation to an API response.

    When exclude_deprecated is True, entities with status='deprecated' are
    hidden from the listing (normal creation flows). Historical views should
    pass exclude_deprecated=False.
    """

    # Subquery: best mapping per object_type_id within the tenant.
    # Prefer tenant-owned datasets over legacy shared datasets.
    mapping_rank = (
        db.query(
            SemanticMappingModel.object_type_id.label("object_type_id"),
            SemanticMappingModel.id.label("mapping_id"),
            func.row_number()
            .over(
                partition_by=SemanticMappingModel.object_type_id,
                order_by=[
                    case((DatasetModel.tenant_id == tenant_id, 1), else_=0).desc(),
                    SemanticMappingModel.version_number.desc(),
                    SemanticMappingModel.updated_at.desc(),
                    SemanticMappingModel.created_at.desc(),
                    SemanticMappingModel.id.desc(),
                ],
            )
            .label("row_num"),
        )
        .outerjoin(DatasetModel, SemanticMappingModel.dataset_id == DatasetModel.id)
        .filter(SemanticMappingModel.tenant_id == tenant_id)
        .subquery()
    )

    # Full best mapping row per object type
    best_mappings = (
        db.query(SemanticMappingModel)
        .join(mapping_rank, SemanticMappingModel.id == mapping_rank.c.mapping_id)
        .filter(mapping_rank.c.row_num == 1)
        .subquery()
    )

    q = (
        db.query(
            ObjectTypeModel.id,
            ObjectTypeModel.object_type_key,
            ObjectTypeModel.display_name,
            ObjectTypeModel.description,
            ObjectTypeModel.plural_name,
            ObjectTypeModel.icon,
            ObjectTypeModel.groups,
            ObjectTypeModel.status,
            ObjectTypeModel.created_at,
            ObjectTypeModel.updated_at,
            best_mappings.c.id.label("mapping_id"),
            best_mappings.c.dataset_id,
            best_mappings.c.dataset_version_id,
            best_mappings.c.version_number.label("mapping_version_number"),
            best_mappings.c.properties,
            best_mappings.c.links,
            best_mappings.c.computed_properties,
            best_mappings.c.updated_at.label("mapping_updated_at"),
            DatasetModel.name.label("dataset_name"),
        )
        .join(
            best_mappings,
            ObjectTypeModel.id == best_mappings.c.object_type_id,
            isouter=True,
        )
        .join(
            DatasetModel,
            best_mappings.c.dataset_id == DatasetModel.id,
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

    if exclude_deprecated:
        q = q.filter(ObjectTypeModel.status != "deprecated")

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
    dataset_id = None
    project_id = None
    if latest:
        ds = db.query(DatasetModel).filter(DatasetModel.id == latest.dataset_id).first()
        if ds:
            dataset_name = ds.name
            dataset_id = ds.id
            project_id = ds.project_id

    return {
        "id": obj.id,
        "tenant_id": obj.tenant_id,
        "object_type_key": obj.object_type_key,
        "display_name": obj.display_name,
        "description": obj.description,
        "plural_name": obj.plural_name or "",
        "icon": obj.icon or "",
        "groups": obj.groups or [],
        "status": obj.status or "in_progress",
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "mapping": latest if latest else None,
        "dataset_name": dataset_name,
        "dataset_id": dataset_id,
        "project_id": project_id,
    }
