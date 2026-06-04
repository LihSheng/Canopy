from typing import Any, overload

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from context.tenant_context import TenantContext
from entity_revision.repository import EntityRevisionRepository
from semantic.entity_registry import (
    get_entity_detail_read_model,
    list_entity_registry_items,
)

router = APIRouter(prefix="/entities", tags=["entities"])


# ─── Response models ───


class EntityRegistryItem(BaseModel):
    id: str
    object_type_key: str
    display_name: str
    description: str
    created_at: str
    updated_at: str | None
    dataset_name: str | None
    dataset_id: str | None
    mapping_version: int | None
    property_count: int
    link_count: int
    computed_property_count: int
    mapping_updated_at: str | None
    # Revision state fields (entity-first model)
    has_published_revision: bool = False
    has_draft: bool = False
    draft_lock_holder_id: str | None = None
    published_revision_number: int | None = None


class PropertyMappingResponse(BaseModel):
    source_column: str
    property_name: str
    semantic_type: str
    included: bool
    is_primary_key: bool


class EntityLinkResponse(BaseModel):
    link_id: str
    display_name: str
    source_property_key: str
    target_object_type_id: str
    target_property_key: str
    cardinality: str


class SourceNodeResponse(BaseModel):
    source_id: str
    source_type: str
    name: str
    reference_id: str
    fields: list[str] = []


class FieldRefResponse(BaseModel):
    source_id: str
    source_name: str
    field_name: str


class ComputedPropertyResponse(BaseModel):
    id: str
    property_name: str
    semantic_type: str
    composition_kind: str
    expression: str
    inputs: list[FieldRefResponse] = []
    included: bool


class EntityDetailResponse(BaseModel):
    id: str
    object_type_key: str
    display_name: str
    description: str
    created_at: str
    updated_at: str | None
    dataset_name: str | None
    dataset_id: str | None = None
    project_id: str | None = None
    mapping: "EntityMappingDetail | None"
    # Revision state fields (entity-first model)
    has_published_revision: bool = False
    has_draft: bool = False
    draft_lock_holder_id: str | None = None
    published_revision_number: int | None = None
    draft_revision_number: int | None = None
    # Revision detail sections — preferred over mapping when available
    published_revision: "EntityRevisionDetail | None" = None
    draft_revision: "EntityRevisionDetail | None" = None


class EntityRevisionPropertyDetail(BaseModel):
    """Canonical entity property from a revision."""

    property_id: str
    property_key: str
    display_name: str
    semantic_type: str
    is_required: bool
    is_primary_key: bool
    sort_order: int


class EntityRevisionDetail(BaseModel):
    """Entity revision content for detail page rendering."""

    id: str
    revision_number: int
    status: str
    properties: list[EntityRevisionPropertyDetail] = []
    source_nodes: list[SourceNodeResponse] = []
    links: list[EntityLinkResponse] = []
    computed_properties: list[ComputedPropertyResponse] = []
    layout_state: dict = {}
    published_at: str | None = None


class EntityMappingDetail(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str
    version_number: int
    properties: list[PropertyMappingResponse]
    links: list[EntityLinkResponse] = []
    source_nodes: list[SourceNodeResponse] = []
    computed_properties: list[ComputedPropertyResponse] = []
    layout_state: dict = {}
    created_at: str
    updated_at: str | None


# ─── Helpers ───


@overload
def _fmt_isofmt(val: object, default: str) -> str: ...
@overload
def _fmt_isofmt(val: object, default: None = None) -> str | None: ...
def _fmt_isofmt(val: Any, default: str | None = None) -> str | None:
    """Format a datetime-like value to ISO string, returning *default* when *val* is falsy."""
    if val is not None:
        iso: str = val.isoformat()
        return iso
    return default


def _build_revision_detail(rev) -> EntityRevisionDetail:
    """Build EntityRevisionDetail from an EntityRevision domain object."""
    return EntityRevisionDetail(
        id=rev.id,
        revision_number=rev.revision_number,
        status=rev.status,
        properties=[
            EntityRevisionPropertyDetail(
                property_id=p.property_id,
                property_key=p.property_key,
                display_name=p.display_name,
                semantic_type=p.semantic_type,
                is_required=p.is_required,
                is_primary_key=p.is_primary_key,
                sort_order=p.sort_order,
            )
            for p in (rev.properties or [])
        ],
        source_nodes=[
            SourceNodeResponse(
                source_id=sn.get("source_id", ""),
                source_type=sn.get("source_type", ""),
                name=sn.get("name", ""),
                reference_id=sn.get("reference_id", ""),
                fields=sn.get("fields", []),
            )
            for sn in (rev.source_nodes or [])
        ],
        links=[
            EntityLinkResponse(
                link_id=ln.get("link_id", ""),
                display_name=ln.get("display_name", ""),
                source_property_key=ln.get("source_property_key", ""),
                target_object_type_id=ln.get("target_object_type_id", ""),
                target_property_key=ln.get("target_property_key", ""),
                cardinality=ln.get("cardinality", ""),
            )
            for ln in (rev.links or [])
        ],
        computed_properties=[
            ComputedPropertyResponse(
                id=cp.get("id", ""),
                property_name=cp.get("property_name", ""),
                semantic_type=cp.get("semantic_type", ""),
                composition_kind=cp.get("composition_kind", ""),
                expression=cp.get("expression", ""),
                included=cp.get("included", False),
                inputs=[
                    FieldRefResponse(
                        source_id=inp.get("source_id", ""),
                        source_name=inp.get("source_name", ""),
                        field_name=inp.get("field_name", ""),
                    )
                    for inp in (cp.get("inputs") or [])
                ],
            )
            for cp in (rev.computed_properties or [])
        ],
        layout_state=rev.layout_state or {},
        published_at=_fmt_isofmt(rev.published_at) if rev.published_at else None,
    )


# ─── Routes ───


@router.get("", response_model=list[EntityRegistryItem])
def list_entities(
    q: str | None = Query(default=None, description="Search by name, key, or dataset"),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    rows = list_entity_registry_items(db, ctx.tenant_id, search=q)
    revision_repo = EntityRevisionRepository(db)

    result: list[EntityRegistryItem] = []
    for row in rows:
        entity_id = row.get("id", "")
        published = revision_repo.get_published(entity_id)
        draft = revision_repo.get_draft(entity_id)

        result.append(
            EntityRegistryItem(
                id=entity_id,
                object_type_key=row.get("object_type_key", ""),
                display_name=row.get("display_name", ""),
                description=row.get("description", ""),
                created_at=_fmt_isofmt(row.get("created_at"), ""),
                updated_at=_fmt_isofmt(row.get("updated_at")),
                dataset_name=row.get("dataset_name"),
                dataset_id=row.get("dataset_id"),
                mapping_version=row.get("mapping_version_number"),
                property_count=len(row.get("properties") or []),
                link_count=len(row.get("links") or []),
                computed_property_count=len(row.get("computed_properties") or []),
                mapping_updated_at=_fmt_isofmt(row.get("mapping_updated_at")),
                has_published_revision=published is not None,
                has_draft=draft is not None,
                draft_lock_holder_id=draft.lock_holder_id if draft else None,
                published_revision_number=published.revision_number if published else None,
            )
        )
    return result


@router.get("/by-dataset/{dataset_id}", response_model=EntityDetailResponse | None)
def get_entity_by_dataset(
    dataset_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Return the entity associated with a dataset, if any.

    Data Studio uses this to surface entity association context.
    """
    from semantic.schema import SemanticMappingModel

    # Find the latest mapping for this dataset within the tenant
    mapping = (
        db.query(SemanticMappingModel)
        .filter(
            SemanticMappingModel.dataset_id == dataset_id,
            SemanticMappingModel.tenant_id == ctx.tenant_id,
        )
        .order_by(SemanticMappingModel.version_number.desc())
        .first()
    )
    if mapping is None:
        return None

    detail = get_entity_detail_read_model(db, ctx.tenant_id, mapping.object_type_id)
    if detail is None:
        return None

    object_type_id = detail["id"]
    revision_repo = EntityRevisionRepository(db)
    published = revision_repo.get_published(object_type_id)
    draft = revision_repo.get_draft(object_type_id)

    mapping_detail = None
    if detail.get("mapping"):
        m = detail["mapping"]
        mapping_detail = EntityMappingDetail(
            id=m.id,
            dataset_id=m.dataset_id,
            dataset_version_id=m.dataset_version_id,
            version_number=m.version_number,
            properties=[
                PropertyMappingResponse(
                    source_column=p.source_column,
                    property_name=p.property_name,
                    semantic_type=p.semantic_type,
                    included=p.included,
                    is_primary_key=p.is_primary_key,
                )
                for p in m.properties
            ],
            links=[
                EntityLinkResponse(
                    link_id=ln.link_id,
                    display_name=ln.display_name,
                    source_property_key=ln.source_property_key,
                    target_object_type_id=ln.target_object_type_id,
                    target_property_key=ln.target_property_key,
                    cardinality=ln.cardinality,
                )
                for ln in (m.links or [])
            ],
            source_nodes=[
                SourceNodeResponse(
                    source_id=sn.source_id,
                    source_type=sn.source_type,
                    name=sn.name,
                    reference_id=sn.reference_id,
                    fields=sn.fields,
                )
                for sn in (m.source_nodes or [])
            ],
            computed_properties=[
                ComputedPropertyResponse(
                    id=cp.id,
                    property_name=cp.property_name,
                    semantic_type=cp.semantic_type,
                    composition_kind=cp.composition_kind,
                    expression=cp.expression,
                    included=cp.included,
                    inputs=[
                        FieldRefResponse(
                            source_id=inp.source_id,
                            source_name=inp.source_name,
                            field_name=inp.field_name,
                        )
                        for inp in (cp.inputs or [])
                    ],
                )
                for cp in (m.computed_properties or [])
            ],
            layout_state=m.layout_state or {},
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else None,
        )

    return EntityDetailResponse(
        id=detail["id"],
        object_type_key=detail["object_type_key"],
        display_name=detail["display_name"],
        description=detail["description"],
        created_at=detail["created_at"].isoformat() if detail.get("created_at") else "",
        updated_at=detail["updated_at"].isoformat() if detail.get("updated_at") else None,
        dataset_name=detail.get("dataset_name"),
        dataset_id=detail.get("dataset_id"),
        project_id=detail.get("project_id"),
        mapping=mapping_detail,
        has_published_revision=published is not None,
        has_draft=draft is not None,
        draft_lock_holder_id=draft.lock_holder_id if draft else None,
        published_revision_number=published.revision_number if published else None,
        draft_revision_number=draft.revision_number if draft else None,
        published_revision=_build_revision_detail(published) if published else None,
        draft_revision=_build_revision_detail(draft) if draft else None,
    )


@router.get("/{object_type_id}", response_model=EntityDetailResponse)
def get_entity(
    object_type_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    detail = get_entity_detail_read_model(db, ctx.tenant_id, object_type_id)
    if detail is None:
        raise NotFoundError("Entity not found")

    revision_repo = EntityRevisionRepository(db)
    published = revision_repo.get_published(object_type_id)
    draft = revision_repo.get_draft(object_type_id)

    mapping_detail = None
    if detail.get("mapping"):
        m = detail["mapping"]
        mapping_detail = EntityMappingDetail(
            id=m.id,
            dataset_id=m.dataset_id,
            dataset_version_id=m.dataset_version_id,
            version_number=m.version_number,
            properties=[
                PropertyMappingResponse(
                    source_column=p.source_column,
                    property_name=p.property_name,
                    semantic_type=p.semantic_type,
                    included=p.included,
                    is_primary_key=p.is_primary_key,
                )
                for p in m.properties
            ],
            links=[
                EntityLinkResponse(
                    link_id=ln.link_id,
                    display_name=ln.display_name,
                    source_property_key=ln.source_property_key,
                    target_object_type_id=ln.target_object_type_id,
                    target_property_key=ln.target_property_key,
                    cardinality=ln.cardinality,
                )
                for ln in (m.links or [])
            ],
            source_nodes=[
                SourceNodeResponse(
                    source_id=sn.source_id,
                    source_type=sn.source_type,
                    name=sn.name,
                    reference_id=sn.reference_id,
                    fields=sn.fields,
                )
                for sn in (m.source_nodes or [])
            ],
            computed_properties=[
                ComputedPropertyResponse(
                    id=cp.id,
                    property_name=cp.property_name,
                    semantic_type=cp.semantic_type,
                    composition_kind=cp.composition_kind,
                    expression=cp.expression,
                    included=cp.included,
                    inputs=[
                        FieldRefResponse(
                            source_id=inp.source_id,
                            source_name=inp.source_name,
                            field_name=inp.field_name,
                        )
                        for inp in (cp.inputs or [])
                    ],
                )
                for cp in (m.computed_properties or [])
            ],
            layout_state=m.layout_state or {},
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else None,
        )

    return EntityDetailResponse(
        id=detail["id"],
        object_type_key=detail["object_type_key"],
        display_name=detail["display_name"],
        description=detail["description"],
        created_at=detail["created_at"].isoformat() if detail.get("created_at") else "",
        updated_at=detail["updated_at"].isoformat() if detail.get("updated_at") else None,
        dataset_name=detail.get("dataset_name"),
        dataset_id=detail.get("dataset_id"),
        project_id=detail.get("project_id"),
        mapping=mapping_detail,
        has_published_revision=published is not None,
        has_draft=draft is not None,
        draft_lock_holder_id=draft.lock_holder_id if draft else None,
        published_revision_number=published.revision_number if published else None,
        draft_revision_number=draft.revision_number if draft else None,
        published_revision=_build_revision_detail(published) if published else None,
        draft_revision=_build_revision_detail(draft) if draft else None,
    )
