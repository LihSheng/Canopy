"""API routes for entity revision lifecycle: draft, publish, list revisions."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError, ValidationError
from context.tenant_context import TenantContext
from entity_formula_engine.engine import FormulaEngine
from entity_revision.deprecation_service import EntityDeprecationService
from entity_revision.domain import ComputedProperty, EntityLink, EntityProperty, SourceBinding
from entity_revision.recovery_service import BindingRecoveryService
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
from semantic.repository import ObjectTypeRepository

router = APIRouter(prefix="/entities", tags=["entity_revisions"])


# ─── Request / Response models ───────────────────────────────────────────


class EntityPropertyRequest(BaseModel):
    """Request shape for a canonical entity property."""

    property_id: str = Field(..., min_length=1, description="Immutable UUID for the property")
    property_key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(..., min_length=1, max_length=255)
    semantic_type: str = "string"
    is_required: bool = False
    is_primary_key: bool = False
    sort_order: int = 0
    format_hint: str = ""


class EntityPropertyResponse(BaseModel):
    """Response shape for a canonical entity property."""

    property_id: str
    property_key: str
    display_name: str
    semantic_type: str
    is_required: bool
    is_primary_key: bool
    sort_order: int
    format_hint: str = ""


class SourceBindingRequest(BaseModel):
    """Request shape for a source-to-property binding."""

    property_key: str = Field(..., min_length=1, description="Entity property key")
    source_node_id: str = Field(..., min_length=1, description="Source node ID")
    source_field_name: str = Field(..., min_length=1, description="Source field name")
    is_active: bool = True


class SourceBindingResponse(BaseModel):
    """Response shape for a source-to-property binding."""

    property_key: str
    source_node_id: str
    source_field_name: str
    is_active: bool = True


class ComputedPropertyResponse(BaseModel):
    """Response shape for a computed property."""

    id: str
    property_key: str
    display_name: str
    formula: str
    formula_type: str = "arithmetic"
    output_type: str = "string"
    sort_order: int = 0
    is_active: bool = True


class SourceDependencyRequest(BaseModel):
    """Pinned source dependency for publish."""

    dependency_type: str = Field(..., description="dataset | dataset_version")
    dependency_id: str = Field(..., min_length=1)


class EntityRevisionResponse(BaseModel):
    """Response shape for an entity revision."""

    id: str
    entity_id: str
    revision_number: int
    status: str
    forked_from_revision_id: str | None = None
    properties: list[EntityPropertyResponse] = []
    source_bindings: list[SourceBindingResponse] = []
    planned_bindings: list[SourceBindingResponse] = []
    links: list[dict] = []
    source_nodes: list[dict] = []
    computed_properties: list[ComputedPropertyResponse] = []
    layout_state: dict = {}
    lock_holder_id: str | None = None
    locked_at: str | None = None
    created_at: str
    updated_at: str
    published_at: str | None = None


class EntityStatusResponse(BaseModel):
    """Summary of entity revision state."""

    has_published: bool
    has_draft: bool
    lock_holder_id: str | None = None
    published_revision_number: int | None = None
    draft_revision_number: int | None = None
    published_at: str | None = None


class ForkDraftRequest(BaseModel):
    """Request to fork a draft from published."""

    # lock_holder_id comes from auth context


class UpdateDraftRequest(BaseModel):
    """Request to update draft content."""

    properties: list[EntityPropertyRequest] | None = None
    source_bindings: list[SourceBindingRequest] | None = None
    planned_bindings: list[SourceBindingRequest] | None = None
    links: list[dict] | None = None
    source_nodes: list[dict] | None = None
    computed_properties: list[dict] | None = None
    layout_state: dict | None = None


class PublishDraftRequest(BaseModel):
    """Request to publish the current draft."""

    source_dependencies: list[SourceDependencyRequest] | None = None


class CreateInitialRevisionRequest(BaseModel):
    """Request to create the initial revision for a new entity."""

    properties: list[EntityPropertyRequest] | None = None
    source_bindings: list[SourceBindingRequest] | None = None
    planned_bindings: list[SourceBindingRequest] | None = None
    links: list[dict] | None = None
    source_nodes: list[dict] | None = None
    computed_properties: list[dict] | None = None
    layout_state: dict | None = None
    publish: bool = False
    source_dependencies: list[SourceDependencyRequest] | None = None


class AddPropertyRequest(BaseModel):
    """Request to add a single property to a draft."""

    property_key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(..., min_length=1, max_length=255)
    semantic_type: str = "string"
    is_required: bool = False
    is_primary_key: bool = False
    sort_order: int = 0


class UpdatePropertyRequest(BaseModel):
    """Request to update a single property in a draft."""

    property_key: str | None = None
    display_name: str | None = None
    semantic_type: str | None = None
    is_required: bool | None = None
    is_primary_key: bool | None = None
    sort_order: int | None = None


class ReorderPropertiesRequest(BaseModel):
    """Request to reorder properties in a draft."""

    property_ids: list[str] = Field(..., min_length=1)


class SetBindingsRequest(BaseModel):
    """Request to set all source bindings for a draft."""

    bindings: list[SourceBindingRequest] = []


class AddComputedPropertyRequest(BaseModel):
    """Request to add a computed property to a draft."""

    property_key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(..., min_length=1, max_length=255)
    formula: str = Field(..., min_length=1)
    formula_type: str = "arithmetic"
    output_type: str = "string"
    sort_order: int = 0
    is_active: bool = True


class UpdateComputedPropertyRequest(BaseModel):
    """Request to update a computed property in a draft."""

    property_key: str | None = None
    display_name: str | None = None
    formula: str | None = None
    formula_type: str | None = None
    output_type: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


# ─── Helpers ──────────────────────────────────────────────────────────────


def _revision_to_response(rev) -> EntityRevisionResponse:
    return EntityRevisionResponse(
        id=rev.id,
        entity_id=rev.entity_id,
        revision_number=rev.revision_number,
        status=rev.status,
        forked_from_revision_id=rev.forked_from_revision_id,
        properties=[
            EntityPropertyResponse(
                property_id=p.property_id,
                property_key=p.property_key,
                display_name=p.display_name,
                semantic_type=p.semantic_type,
                is_required=p.is_required,
                is_primary_key=p.is_primary_key,
                sort_order=p.sort_order,
                format_hint=p.format_hint,
            )
            for p in (rev.properties or [])
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
        links=[lnk.to_dict() if hasattr(lnk, "to_dict") else lnk for lnk in (rev.links or [])],
        source_nodes=rev.source_nodes or [],
        computed_properties=[
            ComputedPropertyResponse(
                id=cp.id,
                property_key=cp.property_key,
                display_name=cp.display_name,
                formula=cp.formula,
                formula_type=cp.formula_type,
                output_type=cp.output_type,
                sort_order=cp.sort_order,
                is_active=cp.is_active,
            )
            for cp in (rev.computed_properties or [])
        ],
        layout_state=rev.layout_state or {},
        lock_holder_id=rev.lock_holder_id,
        locked_at=rev.locked_at.isoformat() if rev.locked_at else None,
        created_at=rev.created_at.isoformat() if rev.created_at else "",
        updated_at=rev.updated_at.isoformat() if rev.updated_at else "",
        published_at=rev.published_at.isoformat() if rev.published_at else None,
    )


def _build_service(db: Session) -> EntityRevisionService:
    revision_repo = EntityRevisionRepository(db)
    object_type_repo = ObjectTypeRepository(db)
    return EntityRevisionService(revision_repo, object_type_repo)


# ─── Routes ───────────────────────────────────────────────────────────────


@router.get("/{entity_id}/revisions/{revision_id}", response_model=EntityRevisionResponse)
def get_revision(
    entity_id: str,
    revision_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Get a single revision by ID, verifying it belongs to the entity."""
    service = _build_service(db)
    try:
        revision = service.get_revision(entity_id, revision_id, ctx.tenant_id)
    except NotFoundError:
        raise
    return _revision_to_response(revision)


@router.get("/{entity_id}/revisions", response_model=list[EntityRevisionResponse])
def list_revisions(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """List all revisions for an entity, ordered by revision_number desc."""
    service = _build_service(db)
    revisions = service.list_revisions(entity_id, ctx.tenant_id)
    return [_revision_to_response(r) for r in revisions]


@router.get("/{entity_id}/status", response_model=EntityStatusResponse)
def get_entity_status(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Get the revision status summary for an entity."""
    service = _build_service(db)
    status = service.get_entity_status(entity_id)
    return EntityStatusResponse(**status)


@router.get("/{entity_id}/draft", response_model=EntityRevisionResponse | None)
def get_draft(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Get the current active draft for an entity, or null if none."""
    service = _build_service(db)
    draft = service.get_draft(entity_id, ctx.tenant_id)
    return _revision_to_response(draft) if draft else None


@router.post("/{entity_id}/draft", status_code=201, response_model=EntityRevisionResponse)
def fork_draft(
    entity_id: str,
    body: ForkDraftRequest | None = None,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Fork a new draft revision from the published revision."""
    service = _build_service(db)
    try:
        draft = service.fork_draft(
            entity_id=entity_id,
            lock_holder_id=user.id,
            tenant_id=ctx.tenant_id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.put("/{entity_id}/draft", response_model=EntityRevisionResponse)
def update_draft(
    entity_id: str,
    body: UpdateDraftRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Update the active draft's content (properties, links, source nodes, etc.)."""
    service = _build_service(db)

    properties_domain = None
    if body.properties is not None:
        properties_domain = [
            EntityProperty(
                property_id=p.property_id,
                property_key=p.property_key,
                display_name=p.display_name,
                semantic_type=p.semantic_type,
                is_required=p.is_required,
                is_primary_key=p.is_primary_key,
                sort_order=p.sort_order,
            )
            for p in body.properties
        ]

    bindings_domain = None
    if body.source_bindings is not None:
        bindings_domain = [
            SourceBinding(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
                is_active=b.is_active,
            )
            for b in body.source_bindings
        ]

    planned_bindings_domain = None
    if body.planned_bindings is not None:
        planned_bindings_domain = [
            SourceBinding(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
                is_active=b.is_active,
            )
            for b in body.planned_bindings
        ]

    computed_properties_domain = None
    if body.computed_properties is not None:
        computed_properties_domain = [
            ComputedProperty(
                id=p.get("id", str(uuid.uuid4())),
                property_key=p.get("property_key", ""),
                display_name=p.get("display_name", ""),
                formula=p.get("formula", ""),
                formula_type=p.get("formula_type", "arithmetic"),
                output_type=p.get("output_type", "string"),
                sort_order=p.get("sort_order", 0),
                is_active=p.get("is_active", True),
            )
            for p in body.computed_properties
        ]

    try:
        draft = service.update_draft(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            properties=properties_domain,
            source_bindings=bindings_domain,
            planned_bindings=planned_bindings_domain,
            links=body.links,
            source_nodes=body.source_nodes,
            computed_properties=computed_properties_domain,
            layout_state=body.layout_state,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


# ─── Property CRUD Routes (within draft) ──────────────────────────────────


@router.post("/{entity_id}/draft/properties", status_code=201, response_model=EntityRevisionResponse)
def add_property(
    entity_id: str,
    body: AddPropertyRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Add a new property to the active draft."""
    service = _build_service(db)
    prop = EntityProperty(
        property_id=str(uuid.uuid4()),
        property_key=body.property_key,
        display_name=body.display_name,
        semantic_type=body.semantic_type,
        is_required=body.is_required,
        is_primary_key=body.is_primary_key,
        sort_order=body.sort_order,
    )
    try:
        draft = service.add_property(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            prop=prop,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.put("/{entity_id}/draft/properties/reorder", response_model=EntityRevisionResponse)
def reorder_properties(
    entity_id: str,
    body: ReorderPropertiesRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Reorder properties in the active draft."""
    service = _build_service(db)
    try:
        draft = service.reorder_properties(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            property_ids=body.property_ids,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.put("/{entity_id}/draft/properties/{property_id}", response_model=EntityRevisionResponse)
def update_property(
    entity_id: str,
    property_id: str,
    body: UpdatePropertyRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Update a single property in the active draft."""
    service = _build_service(db)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise ValidationError("No update fields provided")
    try:
        draft = service.update_property(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            property_id=property_id,
            updates=updates,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.delete("/{entity_id}/draft/properties/{property_id}", response_model=EntityRevisionResponse)
def remove_property(
    entity_id: str,
    property_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Remove a property from the active draft."""
    service = _build_service(db)
    try:
        draft = service.remove_property(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            property_id=property_id,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


# ─── Source Binding Routes ───────────────────────────────────────────────


@router.put("/{entity_id}/draft/bindings", response_model=EntityRevisionResponse)
def set_source_bindings(
    entity_id: str,
    body: SetBindingsRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Set (replace) all source bindings for the active draft."""
    service = _build_service(db)
    bindings_domain = [
        SourceBinding(
            property_key=b.property_key,
            source_node_id=b.source_node_id,
            source_field_name=b.source_field_name,
        )
        for b in body.bindings
    ]
    try:
        draft = service.update_draft(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            source_bindings=bindings_domain,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.get("/{entity_id}/draft/bindings", response_model=list[SourceBindingResponse])
def get_source_bindings(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Get all source bindings for the active draft."""
    service = _build_service(db)
    draft = service.get_draft(entity_id, ctx.tenant_id)
    if draft is None:
        raise NotFoundError("No active draft found")
    return [
        SourceBindingResponse(
            property_key=b.property_key,
            source_node_id=b.source_node_id,
            source_field_name=b.source_field_name,
        )
        for b in (draft.source_bindings or [])
    ]


@router.get("/{entity_id}/draft/bindings/broken", response_model=list[SourceBindingResponse])
def get_broken_bindings(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Get bindings that reference missing properties or source nodes."""
    service = _build_service(db)
    draft = service.get_draft(entity_id, ctx.tenant_id)
    if draft is None:
        raise NotFoundError("No active draft found")

    property_keys = {p.property_key for p in draft.properties}
    source_node_ids = {sn.get("source_id", "") for sn in draft.source_nodes}

    broken: list[SourceBindingResponse] = []
    for b in draft.source_bindings or []:
        is_broken = False
        if b.property_key not in property_keys:
            is_broken = True
        if b.source_node_id not in source_node_ids:
            is_broken = True
        if is_broken:
            broken.append(
                SourceBindingResponse(
                    property_key=b.property_key,
                    source_node_id=b.source_node_id,
                    source_field_name=b.source_field_name,
                )
            )
    return broken


# ─── Draft lifecycle routes ──────────────────────────────────────────────


@router.delete("/{entity_id}/draft")
def discard_draft(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Discard the active draft revision."""
    service = _build_service(db)
    try:
        result = service.discard_draft(entity_id, ctx.tenant_id, lock_holder_id=user.id)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return result


@router.post("/{entity_id}/draft/publish", response_model=EntityRevisionResponse)
def publish_draft(
    entity_id: str,
    body: PublishDraftRequest | None = None,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Publish the current draft revision."""
    service = _build_service(db)

    source_deps = None
    if body and body.source_dependencies:
        source_deps = [d.model_dump() for d in body.source_dependencies]

    try:
        published = service.publish_draft(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            source_dependencies=source_deps,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(published)


@router.post("/{entity_id}/revert/{revision_id}", status_code=201, response_model=EntityRevisionResponse)
def revert_to_revision(
    entity_id: str,
    revision_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Revert to a prior revision by creating a new draft based on it.

    Creates a new draft with the content of the specified historical revision.
    The original revision is never mutated. The user can review and publish
    the reverted state as a new version.
    """
    service = _build_service(db)
    try:
        draft = service.revert_to_revision(
            entity_id=entity_id,
            revision_id=revision_id,
            tenant_id=ctx.tenant_id,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.post("/{entity_id}/revisions", status_code=201, response_model=EntityRevisionResponse)
def create_initial_revision(
    entity_id: str,
    body: CreateInitialRevisionRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Create the initial revision for an entity (blank canvas entrypoint)."""
    service = _build_service(db)

    properties_domain = None
    if body.properties is not None:
        properties_domain = [
            EntityProperty(
                property_id=p.property_id,
                property_key=p.property_key,
                display_name=p.display_name,
                semantic_type=p.semantic_type,
                is_required=p.is_required,
                is_primary_key=p.is_primary_key,
                sort_order=p.sort_order,
            )
            for p in body.properties
        ]

    bindings_domain = None
    if body.source_bindings is not None:
        bindings_domain = [
            SourceBinding(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
                is_active=b.is_active,
            )
            for b in body.source_bindings
        ]

    planned_bindings_domain = None
    if body.planned_bindings is not None:
        planned_bindings_domain = [
            SourceBinding(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
                is_active=b.is_active,
            )
            for b in body.planned_bindings
        ]

    computed_properties_domain = None
    if body.computed_properties is not None:
        computed_properties_domain = [
            ComputedProperty(
                id=p.get("id", str(uuid.uuid4())),
                property_key=p.get("property_key", ""),
                display_name=p.get("display_name", ""),
                formula=p.get("formula", ""),
                formula_type=p.get("formula_type", "arithmetic"),
                output_type=p.get("output_type", "string"),
                sort_order=p.get("sort_order", 0),
                is_active=p.get("is_active", True),
            )
            for p in body.computed_properties
        ]

    source_deps = None
    if body.source_dependencies:
        source_deps = [d.model_dump() for d in body.source_dependencies]

    try:
        revision = service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            properties=properties_domain,
            source_bindings=bindings_domain,
            planned_bindings=planned_bindings_domain,
            links=body.links,
            source_nodes=body.source_nodes,
            computed_properties=computed_properties_domain,
            layout_state=body.layout_state,
            lock_holder_id=user.id,
            publish=body.publish,
            source_dependencies=source_deps,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(revision)


# ─── Link CRUD Routes ────────────────────────────────────────────────────


class EntityLinkRequest(BaseModel):
    link_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    source_property_key: str = Field(..., min_length=1)
    target_entity_id: str = Field(..., min_length=1)
    target_property_key: str = Field(..., min_length=1)
    cardinality: str = Field(..., pattern=r"^(1:1|1:M)$")
    is_optional: bool = False
    is_active: bool = True


class EntityLinkResponse(BaseModel):
    link_id: str
    display_name: str
    source_property_key: str
    target_entity_id: str
    target_property_key: str
    cardinality: str
    is_optional: bool
    is_active: bool


@router.post("/{entity_id}/draft/links", status_code=201, response_model=EntityRevisionResponse)
def add_link(
    entity_id: str,
    body: EntityLinkRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Add a new link to the active draft."""
    service = _build_service(db)
    link = EntityLink(
        link_id=body.link_id,
        display_name=body.display_name,
        source_property_key=body.source_property_key,
        target_entity_id=body.target_entity_id,
        target_property_key=body.target_property_key,
        cardinality=body.cardinality,
        is_optional=body.is_optional,
        is_active=body.is_active,
    )
    try:
        draft = service.add_link(entity_id, ctx.tenant_id, link, lock_holder_id=user.id)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.put("/{entity_id}/draft/links/{link_id}", response_model=EntityRevisionResponse)
def update_link(
    entity_id: str,
    link_id: str,
    body: EntityLinkRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Update a link in the active draft."""
    service = _build_service(db)
    updates = body.model_dump(exclude={"link_id"})
    try:
        draft = service.update_link(entity_id, ctx.tenant_id, link_id, updates, lock_holder_id=user.id)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.delete("/{entity_id}/draft/links/{link_id}", response_model=EntityRevisionResponse)
def remove_link(
    entity_id: str,
    link_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Remove a link from the active draft."""
    service = _build_service(db)
    try:
        draft = service.remove_link(entity_id, ctx.tenant_id, link_id, lock_holder_id=user.id)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.get("/{entity_id}/draft/links", response_model=list[EntityLinkResponse])
def list_links(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """List all links from the active draft or published revision."""
    service = _build_service(db)
    try:
        links = service.list_links(entity_id, ctx.tenant_id)
    except NotFoundError:
        raise
    return [
        EntityLinkResponse(
            link_id=lnk.link_id,
            display_name=lnk.display_name,
            source_property_key=lnk.source_property_key,
            target_entity_id=lnk.target_entity_id,
            target_property_key=lnk.target_property_key,
            cardinality=lnk.cardinality,
            is_optional=lnk.is_optional,
            is_active=lnk.is_active,
        )
        for lnk in links
    ]


# ─── Computed Property CRUD Routes ────────────────────────────────────────


@router.post("/{entity_id}/draft/computed-properties", status_code=201, response_model=EntityRevisionResponse)
def add_computed_property(
    entity_id: str,
    body: AddComputedPropertyRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Add a computed property to the active draft."""
    service = _build_service(db)
    prop = ComputedProperty(
        id=str(uuid.uuid4()),
        property_key=body.property_key,
        display_name=body.display_name,
        formula=body.formula,
        formula_type=body.formula_type,
        output_type=body.output_type,
        sort_order=body.sort_order,
        is_active=body.is_active,
    )
    try:
        draft = service.add_computed_property(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            prop=prop,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.put("/{entity_id}/draft/computed-properties/{computed_property_id}", response_model=EntityRevisionResponse)
def update_computed_property(
    entity_id: str,
    computed_property_id: str,
    body: UpdateComputedPropertyRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Update a computed property in the active draft."""
    service = _build_service(db)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise ValidationError("No update fields provided")
    try:
        draft = service.update_computed_property(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            computed_property_id=computed_property_id,
            updates=updates,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.delete("/{entity_id}/draft/computed-properties/{computed_property_id}", response_model=EntityRevisionResponse)
def remove_computed_property(
    entity_id: str,
    computed_property_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Remove a computed property from the active draft."""
    service = _build_service(db)
    try:
        draft = service.remove_computed_property(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            computed_property_id=computed_property_id,
            lock_holder_id=user.id,
        )
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(draft)


@router.get("/{entity_id}/draft/computed-properties", response_model=list[ComputedPropertyResponse])
def list_computed_properties(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """List computed properties from the active draft or published revision."""
    service = _build_service(db)
    try:
        props = service.list_computed_properties(entity_id, ctx.tenant_id)
    except NotFoundError:
        raise
    return [
        ComputedPropertyResponse(
            id=p.id,
            property_key=p.property_key,
            display_name=p.display_name,
            formula=p.formula,
            formula_type=p.formula_type,
            output_type=p.output_type,
            sort_order=p.sort_order,
            is_active=p.is_active,
        )
        for p in props
    ]


class EvaluateComputedPropertyRequest(BaseModel):
    """Request to evaluate a computed property formula against a sample row."""

    formula: str
    sample_row: dict = {}


class EvaluateComputedPropertyResponse(BaseModel):
    """Response for computed property formula evaluation."""

    result: object | None = None
    errors: list[str] = []
    warnings: list[str] = []


@router.post("/{entity_id}/computed-properties/evaluate", response_model=EvaluateComputedPropertyResponse)
def evaluate_computed_property(
    entity_id: str,
    body: EvaluateComputedPropertyRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Evaluate a computed property formula against a sample row.

    This is a draft helper that allows users to test their formula before saving.
    """
    service = _build_service(db)
    obj = service._object_type_repo.get(entity_id, tenant_id=ctx.tenant_id)
    if obj is None:
        raise NotFoundError("Entity not found")

    errors: list[str] = []
    result = None
    try:
        result = FormulaEngine().evaluate(body.formula, body.sample_row)
    except ValidationError as e:
        errors.append(str(e))

    warnings: list[str] = []
    return EvaluateComputedPropertyResponse(
        result=result,
        errors=errors,
        warnings=warnings,
    )


# ─── Recovery mapping routes ──────────────────────────────────────────────


@router.get("/{entity_id}/draft/bindings/recover", response_model=dict)
def get_recovery_suggestions(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Get recovery suggestions for broken bindings in the active draft."""
    rev_repo = EntityRevisionRepository(db)
    draft = rev_repo.get_draft(entity_id)
    if draft is None:
        raise NotFoundError("No active draft found")
    recovery = BindingRecoveryService(rev_repo)
    return recovery.get_recovery_suggestions(entity_id, draft.id)


@router.put("/{entity_id}/draft/bindings/recover", response_model=EntityRevisionResponse)
def apply_recovery_mapping(
    entity_id: str,
    body: dict,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Apply recovery mapping to broken bindings in the active draft."""
    rev_repo = EntityRevisionRepository(db)
    draft = rev_repo.get_draft(entity_id)
    if draft is None:
        raise NotFoundError("No active draft found")
    recovery = BindingRecoveryService(rev_repo)
    try:
        updated = recovery.apply_recovery(entity_id, draft.id, body)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    return _revision_to_response(updated)


# ─── Deprecation route ──────────────────────────────────────────────────────


class DeprecateEntityResponse(BaseModel):
    """Response after deprecating an entity."""

    entity_id: str
    status: str
    deprecated: bool


@router.post("/{entity_id}/deprecate", response_model=DeprecateEntityResponse)
def deprecate_entity(
    entity_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    """Mark an entity as deprecated. Keeps published revision intact for audit."""
    object_type_repo = ObjectTypeRepository(db)
    service = EntityDeprecationService(object_type_repo)
    entity = service.deprecate_entity(entity_id, ctx.tenant_id)
    return DeprecateEntityResponse(
        entity_id=entity.id,
        status=entity.status,
        deprecated=True,
    )
