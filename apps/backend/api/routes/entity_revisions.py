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
from entity_revision.domain import EntityProperty, SourceBinding
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


class EntityPropertyResponse(BaseModel):
    """Response shape for a canonical entity property."""

    property_id: str
    property_key: str
    display_name: str
    semantic_type: str
    is_required: bool
    is_primary_key: bool
    sort_order: int


class SourceBindingRequest(BaseModel):
    """Request shape for a source-to-property binding."""

    property_key: str = Field(..., min_length=1, description="Entity property key")
    source_node_id: str = Field(..., min_length=1, description="Source node ID")
    source_field_name: str = Field(..., min_length=1, description="Source field name")


class SourceBindingResponse(BaseModel):
    """Response shape for a source-to-property binding."""

    property_key: str
    source_node_id: str
    source_field_name: str


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
    links: list[dict] = []
    source_nodes: list[dict] = []
    computed_properties: list[dict] = []
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
            )
            for p in (rev.properties or [])
        ],
        source_bindings=[
            SourceBindingResponse(
                property_key=b.property_key,
                source_node_id=b.source_node_id,
                source_field_name=b.source_field_name,
            )
            for b in (rev.source_bindings or [])
        ],
        links=rev.links or [],
        source_nodes=rev.source_nodes or [],
        computed_properties=rev.computed_properties or [],
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
            )
            for b in body.source_bindings
        ]

    try:
        draft = service.update_draft(
            entity_id=entity_id,
            tenant_id=ctx.tenant_id,
            properties=properties_domain,
            source_bindings=bindings_domain,
            links=body.links,
            source_nodes=body.source_nodes,
            computed_properties=body.computed_properties,
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
            )
            for b in body.source_bindings
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
            links=body.links,
            source_nodes=body.source_nodes,
            computed_properties=body.computed_properties,
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
