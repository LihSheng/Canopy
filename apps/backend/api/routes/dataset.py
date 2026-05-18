import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from connection.repository import ConnectionRepository
from dataset.cleaning import clean_source_file
from dataset.domain import DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetService, DatasetVersionService
from run.repository import RunRepository

router = APIRouter(prefix="/datasets", tags=["datasets"])


class CreateDatasetRequest(BaseModel):
    project_id: str
    connection_id: str
    name: str
    source_object_name: str = ""


class CreateVersionRequest(BaseModel):
    run_id: str | None = None


def _resolve_static_source_file_path(connection, db: Session) -> str:
    source_file_path = connection.config_json.get("source_file_path")
    if isinstance(source_file_path, str) and source_file_path:
        return source_file_path

    upload_id = connection.config_json.get("upload_id")
    if not isinstance(upload_id, str) or not upload_id:
        return ""

    try:
        return (
            db.execute(
                text("select storage_path from uploads where id = :upload_id"),
                {"upload_id": upload_id},
            ).scalar_one_or_none()
            or ""
        )
    except SQLAlchemyError:
        return ""


def _hydrate_dataset_version(
    dataset,
    db: Session,
):
    version_repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)

    if dataset.active_version_id:
        return dataset

    latest_version = version_repo.get_latest_by_dataset(dataset.id)
    if latest_version is not None:
        return dataset_repo.update_active_version(dataset.id, latest_version.id) or dataset

    connection = ConnectionRepository(db).get(dataset.connection_id)
    if connection is None:
        return dataset

    source_file_path = _resolve_static_source_file_path(connection, db)
    if connection.source_type != "static_file" or not source_file_path:
        return dataset

    result = clean_source_file(
        source_file_path=Path(source_file_path),
        sheet_name=dataset.source_object_name or dataset.name,
        dataset_id=dataset.id,
    )
    version_number = 1
    if latest_version is not None:
        version_number = latest_version.version_number + 1

    version = version_repo.save(
        DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            run_id=None,
            version_number=version_number,
            status=DatasetVersionStatus.READY.value,
            row_count=result["row_count"],
            column_count=result["column_count"],
            storage_path=result["cleaned_path"],
            raw_storage_path=result["raw_path"],
            cleaning_issues=result["cleaning_issues"],
        ),
    )
    return dataset_repo.update_active_version(dataset.id, version.id) or dataset


@router.get("/")
def list_datasets(project_id: str = Query(""), db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    if project_id:
        return service.list_datasets(project_id)
    return service.list_all_datasets()


@router.post("/", status_code=201)
def create_dataset(body: CreateDatasetRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetService(dataset_repo, version_repo)
    dataset = service.create_dataset(
        project_id=body.project_id,
        connection_id=body.connection_id,
        name=body.name,
        source_object_name=body.source_object_name,
    )

    connection = ConnectionRepository(db).get(body.connection_id)
    if connection is not None:
        source_file_path = _resolve_static_source_file_path(connection, db)
        if connection.source_type == "static_file" and source_file_path:
            result = clean_source_file(
                source_file_path=Path(source_file_path),
                sheet_name=body.source_object_name or body.name,
                dataset_id=dataset.id,
            )
            version = version_repo.save(
                DatasetVersion(
                    id=str(uuid.uuid4()),
                    dataset_id=dataset.id,
                    run_id=None,
                    version_number=1,
                    status=DatasetVersionStatus.READY.value,
                    row_count=result["row_count"],
                    column_count=result["column_count"],
                    storage_path=result["cleaned_path"],
                    raw_storage_path=result["raw_path"],
                    cleaning_issues=result["cleaning_issues"],
                ),
            )
            dataset = dataset_repo.update_active_version(dataset.id, version.id) or dataset

    return dataset


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


@router.post("/{id}/versions", status_code=201)
def create_version(id: str, body: CreateVersionRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetVersionService(repo, dataset_repo)
    return service.create_version(dataset_id=id, run_id=body.run_id)


@router.get("/{id}/preview")
def preview_dataset(
    id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    search: str = Query(""),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    dataset_repo = DatasetRepository(db)
    version_repo = DatasetVersionRepository(db)
    dataset = dataset_repo.get(id)
    if dataset is None:
        raise NotFoundError("Dataset not found")

    dataset = _hydrate_dataset_version(dataset, db)

    version = version_repo.get_active_version(id, dataset.active_version_id)
    if version is None or not version.storage_path:
        return {"columns": [], "rows": [], "total_row_count": 0, "filtered_row_count": 0, "page": page, "page_size": page_size}

    from dataset.preview_service import read_dataset_preview

    return read_dataset_preview(
        storage_path=version.storage_path,
        page=page,
        page_size=page_size,
        search=search or None,
    )


@router.get("/{id}/lineage")
def get_lineage(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    dataset_repo = DatasetRepository(db)
    dataset = dataset_repo.get(id)
    if dataset is None:
        raise NotFoundError("Dataset not found")

    run_repo = RunRepository(db)
    runs = run_repo.list_by_dataset(id)

    version_repo = DatasetVersionRepository(db)
    versions = version_repo.list_by_dataset(id)

    nodes: list[dict] = []
    edges: list[dict] = []

    connection = ConnectionRepository(db).get(dataset.connection_id)

    if dataset.source_object_name:
        nodes.append({"id": f"source_{id}", "type": "source_object", "label": dataset.source_object_name})

    if connection is not None:
        nodes.append({"id": f"connection_{dataset.connection_id}", "type": "connection", "label": connection.name})

    nodes.append({"id": f"dataset_{id}", "type": "dataset", "label": dataset.name})

    if dataset.source_object_name and connection is not None:
        edges.append({"from": f"source_{id}", "to": f"connection_{dataset.connection_id}", "type": "feeds"})

    if connection is not None:
        edges.append({"from": f"connection_{dataset.connection_id}", "to": f"dataset_{id}", "type": "provides"})

    for v in versions:
        nodes.append({"id": f"version_{v.id}", "type": "version", "label": f"v{v.version_number}"})
        edges.append({"from": f"version_{v.id}", "to": f"dataset_{id}", "type": "belongs_to"})

    for r in runs:
        nodes.append({"id": f"run_{r.id}", "type": "run", "label": r.status})
        edges.append({"from": f"run_{r.id}", "to": f"dataset_{id}", "type": "produces"})

    return {"nodes": nodes, "edges": edges}


@router.get("/{id}/health")
def get_dataset_health(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    version_repo = DatasetVersionRepository(db)
    service = DatasetService(DatasetRepository(db), version_repo)
    return service.get_dataset_health(id)

