from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError, ValidationError
from connection.importer import build_sheet_profiles, save_uploaded_file
from connection.preview import delete_uploaded_file
from connection.repository import ConnectionRepository
from connection.service import ConnectionService
from context.authorization import verify_tenant_ownership
from context.tenant_context import TenantContext
from control_plane.audit_service import AuditService
from dataset.repository import DatasetRepository
from ingestion.landing_guard import reject_transform_keys
from lineage.metadata_service import LineageMetadataService

router = APIRouter(prefix="/connections", tags=["connections"])


async def _raw_json(request: Request) -> dict[str, Any]:
    result: dict[str, Any] = await request.json()
    return result


class CreateConnectionRequest(BaseModel):
    project_id: str
    source_type: str
    name: str
    config_json: dict = Field(default_factory=dict)


class UpdateConnectionNameRequest(BaseModel):
    name: str


class SheetProfileResponse(BaseModel):
    sheet_name: str
    row_count: int
    data_row_count: int
    column_count: int
    header_row_index: int | None
    confidence: float
    warnings: list[str]
    preview_columns: list[str]
    preview_rows: list[list[object | None]]


class StaticFilePreviewResponse(BaseModel):
    source_file_path: str
    file_name: str
    sheet_profiles: list[SheetProfileResponse]


class DeleteStaticFilePreviewRequest(BaseModel):
    source_file_path: str


def _build_service(db: Session, with_audit: bool = False) -> ConnectionService:
    return ConnectionService(ConnectionRepository(db), AuditService(db) if with_audit else None)


def _lifecycle_service(db: Session) -> ConnectionService:
    return _build_service(db, with_audit=True)


@router.get("/")
def list_connections(
    project_id: str = Query(""),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    if project_id:
        return service.list_connections(project_id, tenant_id=ctx.tenant_id)
    return service.list_all_connections(tenant_id=ctx.tenant_id)


@router.post("/", status_code=201)
async def create_connection(
    body: CreateConnectionRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
    raw_body: dict = Depends(_raw_json),
):
    reject_transform_keys(raw_body, label="connection")
    service = _build_service(db)
    return service.create_connection(
        tenant_id=ctx.tenant_id,
        project_id=body.project_id,
        source_type=body.source_type,
        name=body.name,
        config_json=body.config_json,
    )


@router.post("/preview")
def preview_static_file(
    file: UploadFile = File(...),
    source_type: str = Form("static_file"),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    if source_type != "static_file":
        raise ValidationError("Only static_file preview is supported")

    storage_path = save_uploaded_file(file)
    sheet_profiles = build_sheet_profiles(storage_path)
    return StaticFilePreviewResponse(
        source_file_path=str(storage_path),
        file_name=file.filename or storage_path.name,
        sheet_profiles=[SheetProfileResponse(**profile) for profile in sheet_profiles],
    )


@router.delete("/preview")
def delete_static_file_preview(
    body: DeleteStaticFilePreviewRequest,
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    delete_uploaded_file(Path(body.source_file_path))
    return {"deleted": True}


@router.get("/{id}")
def get_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    connection = service.get_connection(id, tenant_id=ctx.tenant_id)
    if connection is None:
        raise NotFoundError("Connection not found")
    verify_tenant_ownership(ctx, connection.tenant_id, "Connection")
    return connection


@router.patch("/{id}")
def update_connection(
    id: str,
    body: UpdateConnectionNameRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.update_connection_name(id=id, name=body.name, tenant_id=ctx.tenant_id)


@router.get("/{id}/lineage")
def get_connection_lineage(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = LineageMetadataService(ConnectionRepository(db), DatasetRepository(db))
    return service.get_connection_lineage(id)


@router.post("/{id}/test")
async def test_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return await service.test_connection(id, tenant_id=ctx.tenant_id)


@router.get("/{id}/discover")
async def discover_tables(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return await service.discover_tables(id, tenant_id=ctx.tenant_id)


@router.get("/{id}/discover/{table:path}")
async def preview_table(
    id: str,
    table: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return await service.preview_table(id, table, tenant_id=ctx.tenant_id)


def _lifecycle_service(db: Session) -> ConnectionService:
    return _build_service(db, with_audit=True)


@router.get("/{id}/dependencies")
def get_connection_dependencies(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    return _lifecycle_service(db).get_dependency_summary(id, tenant_id=ctx.tenant_id)


@router.post("/{id}/pause")
def pause_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    return _lifecycle_service(db).pause_connection(id, user.id, tenant_id=ctx.tenant_id)


@router.post("/{id}/archive")
def archive_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    return _lifecycle_service(db).archive_connection(id, user.id, tenant_id=ctx.tenant_id)


@router.post("/{id}/restore")
def restore_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    return _lifecycle_service(db).restore_connection(id, user.id, tenant_id=ctx.tenant_id)


@router.post("/{id}/soft-delete")
def soft_delete_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    return _lifecycle_service(db).soft_delete_connection(id, user.id, tenant_id=ctx.tenant_id)


@router.delete("/{id}/permanent")
@router.delete("/{id}")
def permanently_delete_connection(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    return _lifecycle_service(db).permanently_delete_connection(id, user.id, tenant_id=ctx.tenant_id)
