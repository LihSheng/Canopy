from typing import Any, overload

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from context.tenant_context import TenantContext
from entity_detail.service import EntityDetailService
from entity_formula_engine.engine import FormulaEngine
from entity_lineage.graph_builder import build_entity_lineage_graph
from entity_link_resolver.service import LinkResolverService
from entity_materialization.repository import EntityMaterializationRepository
from entity_materialization.service import EntityMaterializationService, build_source_data_reader
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
    plural_name: str = ""
    icon: str = ""
    groups: list[str] = []
    status: str = "in_progress"
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


class SourceBindingResponse(BaseModel):
    property_key: str
    source_node_id: str
    source_field_name: str
    is_active: bool = True


class ComputedPropertyResponse(BaseModel):
    id: str
    property_name: str = ""
    property_key: str = ""
    display_name: str = ""
    semantic_type: str = ""
    composition_kind: str = ""
    formula: str = ""
    formula_type: str = ""
    expression: str = ""
    inputs: list[FieldRefResponse | str] = []
    included: bool = False
    is_active: bool = True
    output_type: str = ""
    sort_order: int = 0


class LineageNodeResponse(BaseModel):
    """A node in the entity-centric lineage graph."""

    id: str
    kind: str  # LineageNodeKind value
    label: str
    properties: list[str] = []
    collapsed: bool = False
    collapsed_count: int = 0
    subtype: str = ""


class LineageEdgeResponse(BaseModel):
    """An edge in the entity-centric lineage graph."""

    id: str
    kind: str  # LineageEdgeKind value
    source_id: str
    target_id: str
    label: str = ""
    source_handle: str = ""
    target_handle: str = ""


class EntityLineageGraphResponse(BaseModel):
    """The complete entity-centered lineage graph read model."""

    entity_id: str
    entity_label: str
    nodes: list[LineageNodeResponse]
    edges: list[LineageEdgeResponse]
    layout_state: dict = {}


class FieldDetailResponse(BaseModel):
    """Unified field detail for base or computed property."""

    field_id: str
    field_kind: str
    property_key: str
    display_name: str
    semantic_type: str
    is_required: bool
    is_primary_key: bool
    sort_order: int
    formula: str | None = None
    formula_type: str | None = None
    is_active: bool = True


class FieldGroupResponse(BaseModel):
    """A named group of fields of a single kind."""

    group_name: str
    field_kind: str
    fields: list[FieldDetailResponse]


class EntityDetailResponse(BaseModel):
    id: str
    object_type_key: str
    display_name: str
    description: str
    plural_name: str = ""
    icon: str = ""
    groups: list[str] = []
    status: str = "in_progress"
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
    # Revision detail sections - preferred over mapping when available
    published_revision: "EntityRevisionDetail | None" = None
    draft_revision: "EntityRevisionDetail | None" = None
    # Pinned version detail (for version pinning endpoint)
    pinned_revision: "EntityRevisionDetail | None" = None
    # Entity-centered lineage graph (PRD 0021)
    lineage: EntityLineageGraphResponse | None = None
    # Issue 6: unified field groups and computed warnings
    field_groups: list[FieldGroupResponse] = []
    materialized_preview: list[dict] = []
    link_status: list[dict] = []


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
    source_bindings: list[SourceBindingResponse] = []
    planned_bindings: list[SourceBindingResponse] = []
    computed_properties: list[ComputedPropertyResponse] = []
    layout_state: dict = {}
    published_at: str | None = None
    # Issue 6: unified field groups and computed warnings
    field_groups: list[FieldGroupResponse] = []
    computed_property_warnings: list[str] = []


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
    from entity_detail.field_model import FieldUnifier

    field_groups = FieldUnifier.group_fields(rev.properties or [], rev.computed_properties or [])
    field_group_responses = [
        FieldGroupResponse(
            group_name=fg.group_name,
            field_kind=fg.field_kind,
            fields=[
                FieldDetailResponse(
                    field_id=f.field_id,
                    field_kind=f.field_kind,
                    property_key=f.property_key,
                    display_name=f.display_name,
                    semantic_type=f.semantic_type,
                    is_required=f.is_required,
                    is_primary_key=f.is_primary_key,
                    sort_order=f.sort_order,
                    formula=f.formula,
                    formula_type=f.formula_type,
                    is_active=f.is_active,
                )
                for f in fg.fields
            ],
        )
        for fg in field_groups
    ]

    # Build computed property warnings for drafts
    computed_property_warnings: list[str] = []
    if rev.status == "draft":
        property_keys = {p.property_key for p in (rev.properties or [])}
        for cp in rev.computed_properties or []:
            if not cp.is_active:
                continue
            try:
                refs = FormulaEngine().extract_property_references(cp.formula)
            except Exception:
                continue
            for ref in refs:
                if ref not in property_keys:
                    computed_property_warnings.append(
                        f"Computed property '{cp.property_key}' references "
                        f"property '{ref}' which is missing or renamed."
                    )

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
                link_id=ln.get("link_id", "") if isinstance(ln, dict) else getattr(ln, "link_id", ""),
                display_name=ln.get("display_name", "") if isinstance(ln, dict) else getattr(ln, "display_name", ""),
                source_property_key=ln.get("source_property_key", "")
                if isinstance(ln, dict)
                else getattr(ln, "source_property_key", ""),
                target_object_type_id=ln.get("target_object_type_id", "")
                if isinstance(ln, dict)
                else getattr(ln, "target_entity_id", ""),
                target_property_key=ln.get("target_property_key", "")
                if isinstance(ln, dict)
                else getattr(ln, "target_property_key", ""),
                cardinality=ln.get("cardinality", "") if isinstance(ln, dict) else getattr(ln, "cardinality", ""),
            )
            for ln in (rev.links or [])
        ],
        source_bindings=[
            SourceBindingResponse(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
                is_active=b.is_active,
            )
            for b in (rev.source_bindings or [])
        ],
        planned_bindings=[
            SourceBindingResponse(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
                is_active=b.is_active,
            )
            for b in (rev.planned_bindings or [])
        ],
        computed_properties=[
            ComputedPropertyResponse(
                id=cp.id,
                property_name=cp.property_key,
                property_key=cp.property_key,
                display_name=cp.display_name,
                formula=cp.formula,
                formula_type=cp.formula_type,
                expression=cp.formula,
                inputs=cp.inputs,
                output_type=cp.output_type,
                sort_order=cp.sort_order,
                is_active=cp.is_active,
            )
            for cp in (rev.computed_properties or [])
        ],
        layout_state=rev.layout_state or {},
        published_at=_fmt_isofmt(rev.published_at) if rev.published_at else None,
        field_groups=field_group_responses,
        computed_property_warnings=computed_property_warnings,
    )


def _build_lineage_response(
    revision,
    entity_display_name: str,
    dataset_id: str | None = None,
    dataset_name: str | None = None,
    dataset_version_id: str | None = None,
    dataset_version_label: str | None = None,
) -> EntityLineageGraphResponse:
    """Build lineage graph response from a revision domain object."""
    graph = build_entity_lineage_graph(
        revision=revision,
        entity_label=entity_display_name,
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        dataset_version_id=dataset_version_id,
        dataset_version_label=dataset_version_label,
    )
    return EntityLineageGraphResponse(
        entity_id=graph.entity_id,
        entity_label=graph.entity_label,
        nodes=[
            LineageNodeResponse(
                id=n.id,
                kind=n.kind.value,
                label=n.label,
                properties=n.properties,
                collapsed=n.collapsed,
                collapsed_count=n.collapsed_count,
                subtype=n.subtype,
            )
            for n in graph.nodes
        ],
        edges=[
            LineageEdgeResponse(
                id=e.id,
                kind=e.kind.value,
                source_id=e.source_id,
                target_id=e.target_id,
                label=e.label,
                source_handle=e.source_handle,
                target_handle=e.target_handle,
            )
            for e in graph.edges
        ],
        layout_state=graph.layout_state,
    )


# ─── Routes ───


@router.get("", response_model=list[EntityRegistryItem])
def list_entities(
    q: str | None = Query(default=None, description="Search by name, key, or dataset"),
    include_deprecated: bool = Query(default=False, description="Include deprecated entities in listing"),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    rows = list_entity_registry_items(db, ctx.tenant_id, search=q, exclude_deprecated=not include_deprecated)
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
                plural_name=row.get("plural_name", "") or "",
                icon=row.get("icon", "") or "",
                groups=row.get("groups", []) or [],
                status=row.get("status", "in_progress") or "in_progress",
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

    # Build entity-centered lineage graph from revision data
    lineage_by_ds = None
    revision_for_lineage_by_ds = published or draft
    if revision_for_lineage_by_ds is not None:
        mapping = detail.get("mapping")
        ds_version_id_by_ds = mapping.dataset_version_id if mapping else None
        ds_version_label_by_ds = f"v{mapping.version_number}" if mapping else None
        lineage_by_ds = _build_lineage_response(
            revision=revision_for_lineage_by_ds,
            entity_display_name=detail["display_name"],
            dataset_id=detail.get("dataset_id"),
            dataset_name=detail.get("dataset_name"),
            dataset_version_id=ds_version_id_by_ds,
            dataset_version_label=ds_version_label_by_ds,
        )

    # Build detail service extras
    detail_service_by_ds = EntityDetailService(
        revision_repo=EntityRevisionRepository(db),
        materialization_repo=EntityMaterializationRepository(db),
        link_resolver=LinkResolverService(
            EntityRevisionRepository(db),
            EntityMaterializationService(
                revision_repo=EntityRevisionRepository(db),
                materialization_repo=EntityMaterializationRepository(db),
                source_data_reader=build_source_data_reader(db),
            ),
        ),
        formula_engine=FormulaEngine(),
    )

    materialized_preview_by_ds = []
    if published is not None:
        materialized_preview_by_ds = detail_service_by_ds.get_entity_preview(
            entity_id=detail["id"], revision_id=published.id
        )

    link_status_by_ds = []
    if published is not None:
        link_status_by_ds = detail_service_by_ds.get_link_status(detail["id"], published)

    return EntityDetailResponse(
        id=detail["id"],
        object_type_key=detail["object_type_key"],
        display_name=detail["display_name"],
        description=detail["description"],
        plural_name=detail.get("plural_name", "") or "",
        icon=detail.get("icon", "") or "",
        groups=detail.get("groups", []) or [],
        status=detail.get("status", "in_progress") or "in_progress",
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
        lineage=lineage_by_ds,
        field_groups=(_build_revision_detail(published) if published else _build_revision_detail(draft)).field_groups
        if (published or draft)
        else [],
        materialized_preview=materialized_preview_by_ds,
        link_status=link_status_by_ds,
    )


# ─── Version pinning routes (must be before /{object_type_id}) ────────────


@router.get("/{entity_id}/versions/latest", response_model=EntityDetailResponse)
def get_latest_published_entity(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Return the entity detail with the latest published revision."""
    detail = get_entity_detail_read_model(db, ctx.tenant_id, entity_id)
    if detail is None:
        raise NotFoundError("Entity not found")

    revision_repo = EntityRevisionRepository(db)
    published = revision_repo.get_published(entity_id)
    if published is None:
        raise NotFoundError("No published revision found for this entity")

    return EntityDetailResponse(
        id=detail["id"],
        object_type_key=detail["object_type_key"],
        display_name=detail["display_name"],
        description=detail["description"],
        plural_name=detail.get("plural_name", "") or "",
        icon=detail.get("icon", "") or "",
        groups=detail.get("groups", []) or [],
        status=detail.get("status", "in_progress") or "in_progress",
        created_at=detail["created_at"].isoformat() if detail.get("created_at") else "",
        updated_at=detail["updated_at"].isoformat() if detail.get("updated_at") else None,
        dataset_name=detail.get("dataset_name"),
        dataset_id=detail.get("dataset_id"),
        project_id=detail.get("project_id"),
        mapping=None,
        has_published_revision=True,
        has_draft=False,
        draft_lock_holder_id=None,
        published_revision_number=published.revision_number,
        draft_revision_number=None,
        published_revision=_build_revision_detail(published),
        draft_revision=None,
        pinned_revision=None,
        lineage=None,
        field_groups=_build_revision_detail(published).field_groups,
        materialized_preview=[],
        link_status=[],
    )


@router.get("/{entity_id}/versions/{revision_number:int}", response_model=EntityDetailResponse)
def get_entity_at_version(
    entity_id: str,
    revision_number: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Return the entity detail pinned to a specific published or archived revision."""
    detail = get_entity_detail_read_model(db, ctx.tenant_id, entity_id)
    if detail is None:
        raise NotFoundError("Entity not found")

    revision_repo = EntityRevisionRepository(db)

    # Find revision by number, rejecting drafts
    revisions = revision_repo.list_by_entity(entity_id)
    pinned = None
    for rev in revisions:
        if rev.revision_number == revision_number:
            if rev.status == "draft":
                raise NotFoundError("Draft revisions cannot be pinned")
            pinned = rev
            break

    if pinned is None:
        raise NotFoundError(f"Revision number {revision_number} not found for this entity")

    return EntityDetailResponse(
        id=detail["id"],
        object_type_key=detail["object_type_key"],
        display_name=detail["display_name"],
        description=detail["description"],
        plural_name=detail.get("plural_name", "") or "",
        icon=detail.get("icon", "") or "",
        groups=detail.get("groups", []) or [],
        status=detail.get("status", "in_progress") or "in_progress",
        created_at=detail["created_at"].isoformat() if detail.get("created_at") else "",
        updated_at=detail["updated_at"].isoformat() if detail.get("updated_at") else None,
        dataset_name=detail.get("dataset_name"),
        dataset_id=detail.get("dataset_id"),
        project_id=detail.get("project_id"),
        mapping=None,
        has_published_revision=True,
        has_draft=False,
        draft_lock_holder_id=None,
        published_revision_number=None,
        draft_revision_number=None,
        published_revision=None,
        draft_revision=None,
        pinned_revision=_build_revision_detail(pinned),
        lineage=None,
        field_groups=_build_revision_detail(pinned).field_groups,
        materialized_preview=[],
        link_status=[],
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

    # Build entity-centered lineage graph from revision data
    lineage = None
    revision_for_lineage = published or draft
    if revision_for_lineage is not None:
        mapping = detail.get("mapping")
        ds_version_id = mapping.dataset_version_id if mapping else None
        ds_version_label = f"v{mapping.version_number}" if mapping else None
        lineage = _build_lineage_response(
            revision=revision_for_lineage,
            entity_display_name=detail["display_name"],
            dataset_id=detail.get("dataset_id"),
            dataset_name=detail.get("dataset_name"),
            dataset_version_id=ds_version_id,
            dataset_version_label=ds_version_label,
        )

    # Build detail service extras
    detail_service = EntityDetailService(
        revision_repo=EntityRevisionRepository(db),
        materialization_repo=EntityMaterializationRepository(db),
        link_resolver=LinkResolverService(
            EntityRevisionRepository(db),
            EntityMaterializationService(
                revision_repo=EntityRevisionRepository(db),
                materialization_repo=EntityMaterializationRepository(db),
                source_data_reader=build_source_data_reader(db),
            ),
        ),
        formula_engine=FormulaEngine(),
    )

    materialized_preview = []
    if published is not None:
        materialized_preview = detail_service.get_entity_preview(entity_id=detail["id"], revision_id=published.id)

    link_status = []
    if published is not None:
        link_status = detail_service.get_link_status(detail["id"], published)

    return EntityDetailResponse(
        id=detail["id"],
        object_type_key=detail["object_type_key"],
        display_name=detail["display_name"],
        description=detail["description"],
        plural_name=detail.get("plural_name", "") or "",
        icon=detail.get("icon", "") or "",
        groups=detail.get("groups", []) or [],
        status=detail.get("status", "in_progress") or "in_progress",
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
        lineage=lineage,
        field_groups=(_build_revision_detail(published) if published else _build_revision_detail(draft)).field_groups
        if (published or draft)
        else [],
        materialized_preview=materialized_preview,
        link_status=link_status,
    )


# ─── Materialization Routes ───────────────────────────────────────────────


class MaterializeRequest(BaseModel):
    revision_id: str | None = None


class MaterializeResponse(BaseModel):
    rows_inserted: int
    rows_updated: int
    rows_tombstoned: int


class MaterializedRowResponse(BaseModel):
    id: str
    entity_id: str
    revision_id: str
    row_id: str
    row_data: dict
    is_tombstone: bool
    materialized_at: str
    deleted_at: str | None = None


@router.post("/{entity_id}/materialize", response_model=MaterializeResponse)
def trigger_materialization(
    entity_id: str,
    body: MaterializeRequest | None = None,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Trigger full snapshot replace materialization for an entity.

    Uses the current published revision by default, or the specified revision_id."""
    service = EntityMaterializationService(
        revision_repo=EntityRevisionRepository(db),
        materialization_repo=EntityMaterializationRepository(db),
        source_data_reader=build_source_data_reader(db),
    )

    revision_id = body.revision_id if body else None
    if revision_id is None:
        revision = EntityRevisionRepository(db).get_published(entity_id)
        if revision is None:
            raise NotFoundError("No published revision found for this entity")
        revision_id = revision.id

    try:
        stats = service.materialize_entity(entity_id, revision_id)
    except NotFoundError:
        raise
    return MaterializeResponse(**stats)


@router.get("/{entity_id}/materialized", response_model=list[MaterializedRowResponse])
def get_materialized_rows(
    entity_id: str,
    version: int | None = Query(default=None, description="Pin to specific revision number"),
    include_tombstones: bool = Query(default=False, description="Include tombstoned rows"),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Return materialized rows for an entity (latest published by default)."""
    service = EntityMaterializationService(
        revision_repo=EntityRevisionRepository(db),
        materialization_repo=EntityMaterializationRepository(db),
        source_data_reader=build_source_data_reader(db),
    )

    revision_id = None
    if version is not None:
        revisions = EntityRevisionRepository(db).list_by_entity(entity_id)
        pinned = None
        for rev in revisions:
            if rev.revision_number == version:
                if rev.status == "draft":
                    raise NotFoundError("Draft revisions cannot be pinned")
                pinned = rev
                break
        if pinned is None:
            raise NotFoundError(f"Revision number {version} not found for this entity")
        revision_id = pinned.id

    rows = service.get_rows(entity_id, revision_id=revision_id, include_tombstones=include_tombstones)
    return [
        MaterializedRowResponse(
            id=r.id,
            entity_id=r.entity_id,
            revision_id=r.revision_id,
            row_id=r.row_id,
            row_data=r.row_data,
            is_tombstone=r.is_tombstone,
            materialized_at=r.materialized_at.isoformat() if r.materialized_at else "",
            deleted_at=r.deleted_at.isoformat() if r.deleted_at else None,
        )
        for r in rows
    ]


@router.get("/{entity_id}/materialized/{row_id}", response_model=MaterializedRowResponse)
def get_materialized_row(
    entity_id: str,
    row_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Return a single materialized row by entity_id + row_id."""
    service = EntityMaterializationService(
        revision_repo=EntityRevisionRepository(db),
        materialization_repo=EntityMaterializationRepository(db),
        source_data_reader=build_source_data_reader(db),
    )
    row = service.get_row(entity_id, row_id)
    if row is None:
        raise NotFoundError("Row not found")
    return MaterializedRowResponse(
        id=row.id,
        entity_id=row.entity_id,
        revision_id=row.revision_id,
        row_id=row.row_id,
        row_data=row.row_data,
        is_tombstone=row.is_tombstone,
        materialized_at=row.materialized_at.isoformat() if row.materialized_at else "",
        deleted_at=row.deleted_at.isoformat() if row.deleted_at else None,
    )


# ─── Link Resolution Routes ───────────────────────────────────────────────


@router.get("/{entity_id}/links/{link_id}/resolve")
def resolve_link(
    entity_id: str,
    link_id: str,
    row_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Resolve a single link for a specific source row."""
    revision_repo = EntityRevisionRepository(db)
    mat_service = EntityMaterializationService(
        revision_repo=revision_repo,
        materialization_repo=EntityMaterializationRepository(db),
        source_data_reader=build_source_data_reader(db),
    )
    resolver = LinkResolverService(revision_repo, mat_service)

    # Get the source row
    source_row = mat_service.get_row(entity_id, row_id)
    if source_row is None:
        raise NotFoundError("Source row not found")

    result = resolver.resolve_link(entity_id, link_id, source_row)
    if result is None:
        from fastapi import Response

        return Response(status_code=204)

    if isinstance(result, list):
        return [
            MaterializedRowResponse(
                id=r.id,
                entity_id=r.entity_id,
                revision_id=r.revision_id,
                row_id=r.row_id,
                row_data=r.row_data,
                is_tombstone=r.is_tombstone,
                materialized_at=r.materialized_at.isoformat() if r.materialized_at else "",
                deleted_at=r.deleted_at.isoformat() if r.deleted_at else None,
            )
            for r in result
        ]

    return MaterializedRowResponse(
        id=result.id,
        entity_id=result.entity_id,
        revision_id=result.revision_id,
        row_id=result.row_id,
        row_data=result.row_data,
        is_tombstone=result.is_tombstone,
        materialized_at=result.materialized_at.isoformat() if result.materialized_at else "",
        deleted_at=result.deleted_at.isoformat() if result.deleted_at else None,
    )


class ResolveBatchRequest(BaseModel):
    row_ids: list[str]


@router.post("/{entity_id}/links/{link_id}/resolve-batch")
def resolve_link_batch(
    entity_id: str,
    link_id: str,
    body: ResolveBatchRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Resolve a link for multiple source rows (batch)."""
    revision_repo = EntityRevisionRepository(db)
    mat_service = EntityMaterializationService(
        revision_repo=revision_repo,
        materialization_repo=EntityMaterializationRepository(db),
        source_data_reader=build_source_data_reader(db),
    )
    resolver = LinkResolverService(revision_repo, mat_service)

    # Fetch source rows
    source_rows = [mat_service.get_row(entity_id, rid) for rid in body.row_ids]
    if any(r is None for r in source_rows):
        missing = [rid for rid, r in zip(body.row_ids, source_rows) if r is None]
        raise NotFoundError(f"Source rows not found: {missing}")

    results = resolver.resolve_link_batch(entity_id, link_id, source_rows)

    def _to_response(row):
        if row is None:
            return None
        if isinstance(row, list):
            return [
                MaterializedRowResponse(
                    id=r.id,
                    entity_id=r.entity_id,
                    revision_id=r.revision_id,
                    row_id=r.row_id,
                    row_data=r.row_data,
                    is_tombstone=r.is_tombstone,
                    materialized_at=r.materialized_at.isoformat() if r.materialized_at else "",
                    deleted_at=r.deleted_at.isoformat() if r.deleted_at else None,
                )
                for r in row
            ]
        return MaterializedRowResponse(
            id=row.id,
            entity_id=row.entity_id,
            revision_id=row.revision_id,
            row_id=row.row_id,
            row_data=row.row_data,
            is_tombstone=row.is_tombstone,
            materialized_at=row.materialized_at.isoformat() if row.materialized_at else "",
            deleted_at=row.deleted_at.isoformat() if row.deleted_at else None,
        )

    return {rid: _to_response(r) for rid, r in results.items()}
