from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from v4.dataset.repository import DatasetRepository, DatasetVersionRepository
from v4.dataset.service import DatasetService, DatasetVersionService
from v4.run.repository import RunRepository

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


class CreateDatasetRequest(BaseModel):
    project_id: str
    connection_id: str
    name: str
    source_object_name: str = ""


class CreateVersionRequest(BaseModel):
    run_id: str | None = None


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
    service = DatasetService(DatasetRepository(db), version_repo)
    return service.create_dataset(
        project_id=body.project_id,
        connection_id=body.connection_id,
        name=body.name,
        source_object_name=body.source_object_name,
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


@router.post("/{id}/versions", status_code=201)
def create_version(id: str, body: CreateVersionRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    repo = DatasetVersionRepository(db)
    dataset_repo = DatasetRepository(db)
    service = DatasetVersionService(repo, dataset_repo)
    return service.create_version(dataset_id=id, run_id=body.run_id)


@router.get("/{id}/preview")
def preview_dataset(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    dataset_repo = DatasetRepository(db)
    version_repo = DatasetVersionRepository(db)
    dataset = dataset_repo.get(id)
    if dataset is None:
        raise NotFoundError("Dataset not found")

    if not dataset.active_version_id:
        return {"columns": [], "rows": [], "total_row_count": 0}

    version = version_repo.get_active_version(id, dataset.active_version_id)
    if version is None or not version.storage_path:
        return {"columns": [], "rows": [], "total_row_count": 0}

    import json
    from pathlib import Path

    path = Path(version.storage_path)
    if not path.exists():
        return {"columns": [], "rows": [], "total_row_count": 0}

    rows: list[dict] = []
    columns: list[str] = []
    with open(str(path), "r") as f:
        for i, line in enumerate(f):
            if i >= 100:
                break
            row = json.loads(line)
            if isinstance(row, dict):
                if not columns:
                    columns = list(row.keys())
                rows.append([row.get(c) for c in columns])
    return {"columns": columns, "rows": rows, "total_row_count": len(rows)}


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

    nodes.append({"id": f"dataset_{id}", "type": "dataset", "label": dataset.name})

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
