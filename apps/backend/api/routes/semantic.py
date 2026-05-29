from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from context.tenant_context import TenantContext
from semantic.domain import Cardinality, EntityLink, PropertyMapping, SemanticMapping
from semantic.repository import ObjectTypeRepository, SemanticMappingRepository
from semantic.schema_service import DatasetSchemaService
from semantic.service import ObjectTypeService, SemanticMappingService

router = APIRouter(prefix="/semantic", tags=["semantic"])


# ─── Pydantic request/response models ───


class ObjectTypeResponse(BaseModel):
    id: str
    tenant_id: str
    object_type_key: str
    display_name: str
    description: str
    created_at: str
    updated_at: str | None


class CreateObjectTypeRequest(BaseModel):
    object_type_key: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str = Field(..., min_length=1, max_length=255)
    description: str = ""


class UpdateObjectTypeRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None


class SchemaColumnResponse(BaseModel):
    column_name: str
    primitive_type: str


class PropertyMappingRequest(BaseModel):
    source_column: str
    property_name: str
    semantic_type: str = "string"
    included: bool = True
    is_primary_key: bool = False


class PropertyMappingResponse(BaseModel):
    source_column: str
    property_name: str
    semantic_type: str
    included: bool
    is_primary_key: bool


class EntityLinkRequest(BaseModel):
    link_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    source_property_key: str = Field(..., min_length=1)
    target_object_type_id: str = Field(..., min_length=1)
    target_property_key: str = ""
    cardinality: str = Cardinality.MANY_TO_ONE


class EntityLinkResponse(BaseModel):
    link_id: str
    display_name: str
    source_property_key: str
    target_object_type_id: str
    target_property_key: str
    cardinality: str


class CreateMappingRequest(BaseModel):
    object_type_id: str
    object_type_key: str
    properties: list[PropertyMappingRequest]
    links: list[EntityLinkRequest] = []


class MappingResponse(BaseModel):
    id: str
    tenant_id: str
    dataset_id: str
    dataset_version_id: str
    version_number: int
    object_type_id: str
    object_type_key: str
    properties: list[PropertyMappingResponse]
    links: list[EntityLinkResponse] = []
    created_at: str
    updated_at: str | None


class ValidationErrorItem(BaseModel):
    field: str
    value: str | None
    message: str


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[ValidationErrorItem]


def _obj_to_response(obj) -> ObjectTypeResponse:
    return ObjectTypeResponse(
        id=obj.id,
        tenant_id=obj.tenant_id,
        object_type_key=obj.object_type_key,
        display_name=obj.display_name,
        description=obj.description,
        created_at=obj.created_at.isoformat() if obj.created_at else "",
        updated_at=obj.updated_at.isoformat() if obj.updated_at else None,
    )


def _mapping_to_response(m: SemanticMapping) -> MappingResponse:
    return MappingResponse(
        id=m.id,
        tenant_id=m.tenant_id,
        dataset_id=m.dataset_id,
        dataset_version_id=m.dataset_version_id,
        version_number=m.version_number,
        object_type_id=m.object_type_id,
        object_type_key=m.object_type_key,
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
        created_at=m.created_at.isoformat() if m.created_at else "",
        updated_at=m.updated_at.isoformat() if m.updated_at else None,
    )


# ─── Object Type Endpoints ───


@router.get("/object-types", response_model=list[ObjectTypeResponse])
def list_object_types(
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = ObjectTypeService(ObjectTypeRepository(db))
    types = service.list_by_tenant(ctx.tenant_id)
    return [_obj_to_response(t) for t in types]


@router.post("/object-types", status_code=201, response_model=ObjectTypeResponse)
def create_object_type(
    body: CreateObjectTypeRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = ObjectTypeService(ObjectTypeRepository(db))
    try:
        obj = service.create(
            tenant_id=ctx.tenant_id,
            object_type_key=body.object_type_key,
            display_name=body.display_name,
            description=body.description,
        )
    except IntegrityError:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Object type key '{body.object_type_key}' already exists for this tenant"},
        )
    return _obj_to_response(obj)


@router.get("/object-types/{id}", response_model=ObjectTypeResponse)
def get_object_type(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = ObjectTypeService(ObjectTypeRepository(db))
    obj = service.get(id)
    if obj is None:
        raise NotFoundError("Object type not found")
    return _obj_to_response(obj)


@router.patch("/object-types/{id}", response_model=ObjectTypeResponse)
def update_object_type(
    id: str,
    body: UpdateObjectTypeRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = ObjectTypeService(ObjectTypeRepository(db))
    obj = service.update(id, display_name=body.display_name, description=body.description)
    return _obj_to_response(obj)


# ─── Schema Endpoint ───


@router.get("/datasets/{dataset_id}/versions/{version_id}/schema", response_model=list[SchemaColumnResponse])
async def get_dataset_schema(
    dataset_id: str,
    version_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    schema_service = DatasetSchemaService(db)
    columns = await schema_service.get_schema(dataset_id, version_id)
    return [SchemaColumnResponse(column_name=c.column_name, primitive_type=c.primitive_type) for c in columns]


# ─── Mapping Endpoints ───


@router.get("/datasets/{dataset_id}/versions/{version_id}/mapping", response_model=MappingResponse | None)
async def get_mapping(
    dataset_id: str,
    version_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    mapping_repo = SemanticMappingRepository(db)
    object_type_repo = ObjectTypeRepository(db)
    schema_service = DatasetSchemaService(db)
    service = SemanticMappingService(mapping_repo, object_type_repo, schema_service)
    mapping = service.get_current(dataset_id, version_id)
    if mapping is None:
        return None
    return _mapping_to_response(mapping)


@router.post("/datasets/{dataset_id}/versions/{version_id}/mapping", status_code=201, response_model=MappingResponse)
async def create_mapping(
    dataset_id: str,
    version_id: str,
    body: CreateMappingRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    mapping_repo = SemanticMappingRepository(db)
    object_type_repo = ObjectTypeRepository(db)
    schema_service = DatasetSchemaService(db)
    service = SemanticMappingService(mapping_repo, object_type_repo, schema_service)

    properties = [
        PropertyMapping(
            source_column=p.source_column,
            property_name=p.property_name,
            semantic_type=p.semantic_type,
            included=p.included,
            is_primary_key=p.is_primary_key,
        )
        for p in body.properties
    ]
    links = [
        EntityLink(
            link_id=ln.link_id,
            display_name=ln.display_name,
            source_property_key=ln.source_property_key,
            target_object_type_id=ln.target_object_type_id,
            target_property_key=ln.target_property_key,
            cardinality=ln.cardinality,
        )
        for ln in body.links
    ]

    mapping = await service.create(
        dataset_id=dataset_id,
        dataset_version_id=version_id,
        object_type_id=body.object_type_id,
        object_type_key=body.object_type_key,
        properties=properties,
        links=links,
    )
    return _mapping_to_response(mapping)


@router.put("/datasets/{dataset_id}/versions/{version_id}/mapping", response_model=MappingResponse)
async def update_mapping(
    dataset_id: str,
    version_id: str,
    body: CreateMappingRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    mapping_repo = SemanticMappingRepository(db)
    object_type_repo = ObjectTypeRepository(db)
    schema_service = DatasetSchemaService(db)
    service = SemanticMappingService(mapping_repo, object_type_repo, schema_service)

    properties = [
        PropertyMapping(
            source_column=p.source_column,
            property_name=p.property_name,
            semantic_type=p.semantic_type,
            included=p.included,
            is_primary_key=p.is_primary_key,
        )
        for p in body.properties
    ]
    links = [
        EntityLink(
            link_id=ln.link_id,
            display_name=ln.display_name,
            source_property_key=ln.source_property_key,
            target_object_type_id=ln.target_object_type_id,
            target_property_key=ln.target_property_key,
            cardinality=ln.cardinality,
        )
        for ln in body.links
    ]

    mapping = await service.update(
        dataset_id=dataset_id,
        dataset_version_id=version_id,
        object_type_id=body.object_type_id,
        object_type_key=body.object_type_key,
        properties=properties,
        links=links,
    )
    return _mapping_to_response(mapping)


@router.post("/datasets/{dataset_id}/versions/{version_id}/mapping/validate", response_model=ValidationResponse)
async def validate_mapping_endpoint(
    dataset_id: str,
    version_id: str,
    body: CreateMappingRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    mapping_repo = SemanticMappingRepository(db)
    object_type_repo = ObjectTypeRepository(db)
    schema_service = DatasetSchemaService(db)
    service = SemanticMappingService(mapping_repo, object_type_repo, schema_service)

    properties = [
        PropertyMapping(
            source_column=p.source_column,
            property_name=p.property_name,
            semantic_type=p.semantic_type,
            included=p.included,
            is_primary_key=p.is_primary_key,
        )
        for p in body.properties
    ]
    links = [
        EntityLink(
            link_id=ln.link_id,
            display_name=ln.display_name,
            source_property_key=ln.source_property_key,
            target_object_type_id=ln.target_object_type_id,
            target_property_key=ln.target_property_key,
            cardinality=ln.cardinality,
        )
        for ln in body.links
    ]

    result = await service.validate(dataset_id, version_id, properties, links=links)
    return ValidationResponse(
        valid=result["valid"],
        errors=[ValidationErrorItem(**e) for e in result["errors"]],
    )
