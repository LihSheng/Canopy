from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_platform_admin, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from context.authorization import verify_tenant_ownership
from context.tenant_context import TenantContext
from control_plane.audit_service import AuditService
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetService, DatasetVersionService
from ingestion.landing_guard import reject_transform_keys
from retention.repository import RetentionPolicyRepository
from retention.service import RetentionPolicyService

router = APIRouter(prefix="/datasets", tags=["datasets"])


async def _raw_json(request: Request) -> dict[str, Any]:
    result: dict[str, Any] = await request.json()
    return result


class CreateDatasetRequest(BaseModel):
    project_id: str
    connection_id: str
    name: str
    source_object_name: str = ""
    defer_materialization: bool = False
    sync_mode: str | None = None
    batch_strategy: str | None = None
    real_time_strategy: str | None = None
    cursor_column: str | None = None
    last_cursor_value: str | None = None


class CreateVersionRequest(BaseModel):
    run_id: str | None = None


class ReimportRequest(BaseModel):
    data_path: str
    columns: list[str]
    sheet_name: str | None = None


class UpdateDatasetNameRequest(BaseModel):
    name: str


class BulkDeleteSummaryRequest(BaseModel):
    dataset_ids: list[str]


class BulkDeleteRequest(BaseModel):
    dataset_ids: list[str]


class SyncPolicyUpdateRequest(BaseModel):
    sync_mode: str | None = None
    batch_strategy: str | None = None
    real_time_strategy: str | None = None
    cursor_column: str | None = None
    frequency_minutes: int | None = None


class DatasetDeleteSummaryResponse(BaseModel):
    dataset_id: str
    version_count: int
    active_run_count: int
    entity_count: int
    can_delete: bool
    blocking_reason: str | None = None


class DatasetVersionDeleteSummaryResponse(BaseModel):
    dataset_id: str
    version_id: str
    version_number: int
    is_active_version: bool
    can_delete: bool
    blocking_reason: str | None = None


def _build_service(db: Session) -> DatasetService:
    version_repo = DatasetVersionRepository(db)
    return DatasetService(DatasetRepository(db), version_repo)


@router.get("/")
def list_datasets(
    project_id: str = Query(""),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    if project_id:
        return service.list_datasets(project_id, tenant_id=ctx.tenant_id)
    return service.list_all_datasets(tenant_id=ctx.tenant_id)


@router.post("/", status_code=201)
async def create_dataset(
    body: CreateDatasetRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
    raw_body: dict = Depends(_raw_json),
):
    reject_transform_keys(raw_body, label="dataset")
    service = _build_service(db)
    return await service.create_dataset_async(
        tenant_id=ctx.tenant_id,
        project_id=body.project_id,
        connection_id=body.connection_id,
        name=body.name,
        source_object_name=body.source_object_name,
        defer_materialization=body.defer_materialization,
        sync_mode=body.sync_mode,
        batch_strategy=body.batch_strategy,
        real_time_strategy=body.real_time_strategy,
        cursor_column=body.cursor_column,
    )


@router.post("/bulk-delete-summary")
def get_bulk_delete_summary(
    body: BulkDeleteSummaryRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.get_bulk_delete_summary(body.dataset_ids, tenant_id=ctx.tenant_id)


@router.post("/bulk-delete")
def bulk_delete_datasets(
    body: BulkDeleteRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.bulk_delete_datasets(body.dataset_ids, tenant_id=ctx.tenant_id)


@router.get("/{id}")
def get_dataset(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    dataset = service.get_dataset(id, tenant_id=ctx.tenant_id)
    if dataset is None:
        raise NotFoundError("Dataset not found")
    verify_tenant_ownership(ctx, dataset.tenant_id, "Dataset")
    return dataset


@router.patch("/{id}")
def update_dataset(
    id: str,
    body: UpdateDatasetNameRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.update_dataset_name(id=id, name=body.name, tenant_id=ctx.tenant_id)


@router.get("/{id}/versions")
def list_versions(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    repo = DatasetVersionRepository(db)
    return repo.list_by_dataset(id)


@router.get("/{id}/dependencies")
def get_delete_summary(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return DatasetDeleteSummaryResponse(**service.get_delete_summary(id, tenant_id=ctx.tenant_id))


@router.get("/{dataset_id}/versions/{version_id}/dependencies")
def get_version_delete_summary(
    dataset_id: str,
    version_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    version_repo = DatasetVersionRepository(db)
    service = DatasetVersionService(version_repo, DatasetRepository(db))
    return DatasetVersionDeleteSummaryResponse(**service.get_delete_summary(dataset_id, version_id))


@router.post("/{id}/versions", status_code=201)
def create_version(
    id: str,
    body: CreateVersionRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetVersionService(repo, dataset_repo)
    return service.create_version(dataset_id=id, run_id=body.run_id)


@router.post("/{id}/reimport", status_code=201)
async def reimport_dataset_version(
    id: str,
    body: ReimportRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
    raw_body: dict = Depends(_raw_json),
):
    reject_transform_keys(raw_body, label="reimport")
    version_repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetVersionService(version_repo, dataset_repo)
    return service.reimport_version(
        dataset_id=id,
        data_path=body.data_path,
        columns=body.columns,
        sheet_name=body.sheet_name,
    )


@router.post("/{id}/refresh", status_code=201)
def refresh_dataset_version(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.refresh_dataset_version(dataset_id=id, tenant_id=ctx.tenant_id)


@router.delete("/{id}")
def delete_dataset(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.delete_dataset(id, tenant_id=ctx.tenant_id)


@router.delete("/{dataset_id}/versions/{version_id}")
def delete_version(
    dataset_id: str,
    version_id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    version_repo = DatasetVersionRepository(db)
    service = DatasetVersionService(version_repo, DatasetRepository(db))
    return service.delete_version(dataset_id, version_id)


@router.get("/{id}/preview")
def preview_dataset(
    id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    search: str = Query(""),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.preview_dataset(id, page, page_size, search, tenant_id=ctx.tenant_id)


@router.get("/{id}/lineage")
def get_lineage(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.get_lineage(id, tenant_id=ctx.tenant_id)


@router.get("/{id}/health")
def get_dataset_health(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.get_dataset_health(id, tenant_id=ctx.tenant_id)


@router.get("/{id}/drift-events")
def get_drift_events(
    id: str,
    limit: int = Query(20, ge=1, le=100),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    from schema_drift.service import SchemaDriftService

    service = SchemaDriftService(db)
    return service.list_drift_events(id, limit=limit)


class ClearBlockRequest(BaseModel):
    actor_user_id: str | None = None


@router.post("/{id}/clear-drift-block")
def clear_drift_block(
    id: str,
    body: ClearBlockRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    from schema_drift.service import SchemaDriftService

    service = SchemaDriftService(db)
    return service.clear_block(dataset_id=id, actor_user_id=body.actor_user_id or user.id)


@router.patch("/{id}/sync-policy")
def update_sync_policy(
    id: str,
    body: SyncPolicyUpdateRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.update_sync_policy(
        dataset_id=id,
        sync_mode=body.sync_mode,
        batch_strategy=body.batch_strategy,
        real_time_strategy=body.real_time_strategy,
        cursor_column=body.cursor_column,
        frequency_minutes=body.frequency_minutes,
        tenant_id=ctx.tenant_id,
    )


class RetentionPolicyRequest(BaseModel):
    preset: str
    mode: str | None = None
    horizon_days: int | None = None


@router.get("/{id}/retention-policy")
def get_retention_policy(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    repo = RetentionPolicyRepository(db)
    service = RetentionPolicyService(repo)
    return service.get_policy(dataset_id=id)


@router.put("/{id}/retention-policy")
def save_retention_policy(
    id: str,
    body: RetentionPolicyRequest,
    admin: SessionUser = Depends(require_platform_admin),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    repo = RetentionPolicyRepository(db)
    audit = AuditService(db)
    service = RetentionPolicyService(repo, audit_service=audit)
    return service.save_policy(
        dataset_id=id,
        tenant_id=ctx.tenant_id,
        actor_user_id=user.id,
        preset=body.preset,
        mode=body.mode,
        horizon_days=body.horizon_days,
    )
