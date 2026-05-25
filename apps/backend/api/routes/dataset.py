from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetService, DatasetVersionService

router = APIRouter(prefix="/datasets", tags=["datasets"])


class CreateDatasetRequest(BaseModel):
    project_id: str
    connection_id: str
    name: str
    source_object_name: str = ""
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
    can_delete: bool
    blocking_reason: str | None = None


class DatasetVersionDeleteSummaryResponse(BaseModel):
    dataset_id: str
    version_id: str
    version_number: int
    is_active_version: bool
    can_delete: bool
    blocking_reason: str | None = None


@router.get("/")
def list_datasets(
    project_id: str = Query(""), db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)
):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    if project_id:
        return service.list_datasets(project_id)
    return service.list_all_datasets()


@router.post("/", status_code=201)
async def create_dataset(
    body: CreateDatasetRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)
):
    service = DatasetService(DatasetRepository(db), DatasetVersionRepository(db))
    return await service.create_dataset_async(
        project_id=body.project_id,
        connection_id=body.connection_id,
        name=body.name,
        source_object_name=body.source_object_name,
        sync_mode=body.sync_mode,
        batch_strategy=body.batch_strategy,
        real_time_strategy=body.real_time_strategy,
        cursor_column=body.cursor_column,
    )


@router.get("/{id}")
def get_dataset(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    dataset = service.get_dataset(id)
    if dataset is None:
        raise NotFoundError("Dataset not found")
    return dataset


@router.get("/{id}/versions")
def list_versions(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    repo = DatasetVersionRepository(db)
    return repo.list_by_dataset(id)


@router.get("/{id}/dependencies")
def get_delete_summary(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    return DatasetDeleteSummaryResponse(**service.get_delete_summary(id))


@router.get("/{dataset_id}/versions/{version_id}/dependencies")
def get_version_delete_summary(
    dataset_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    version_repo = DatasetVersionRepository(db)
    service = DatasetVersionService(version_repo, DatasetRepository(db))
    return DatasetVersionDeleteSummaryResponse(**service.get_delete_summary(dataset_id, version_id))


@router.post("/{id}/versions", status_code=201)
def create_version(
    id: str, body: CreateVersionRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)
):
    repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetVersionService(repo, dataset_repo)
    return service.create_version(dataset_id=id, run_id=body.run_id)


@router.post("/{id}/reimport", status_code=201)
def reimport_dataset_version(
    id: str,
    body: ReimportRequest,
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    version_repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetVersionService(version_repo, dataset_repo)
    return service.reimport_version(
        dataset_id=id,
        data_path=body.data_path,
        columns=body.columns,
        sheet_name=body.sheet_name,
    )


@router.delete("/{id}")
def delete_dataset(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    return service.delete_dataset(id)


@router.delete("/{dataset_id}/versions/{version_id}")
def delete_version(
    dataset_id: str,
    version_id: str,
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
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = DatasetService(DatasetRepository(db), DatasetVersionRepository(db))
    return service.preview_dataset(id, page, page_size, search)


@router.get("/{id}/lineage")
def get_lineage(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = DatasetService(DatasetRepository(db), DatasetVersionRepository(db))
    return service.get_lineage(id)


@router.get("/{id}/health")
def get_dataset_health(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    return service.get_dataset_health(id)


@router.patch("/{id}/sync-policy")
def update_sync_policy(
    id: str,
    body: SyncPolicyUpdateRequest,
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    return service.update_sync_policy(
        dataset_id=id,
        sync_mode=body.sync_mode,
        batch_strategy=body.batch_strategy,
        real_time_strategy=body.real_time_strategy,
        cursor_column=body.cursor_column,
        frequency_minutes=body.frequency_minutes,
    )
