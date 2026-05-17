from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from v4.run.repository import RunRepository
from v4.run.service import RunService

router = APIRouter(prefix="/api/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    project_id: str
    connection_id: str
    dataset_id: str
    started_by: str = ""


@router.get("/")
def list_runs(project_id: str = Query(...), db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = RunService(RunRepository(db))
    return service.list_runs_by_project(project_id)


@router.post("/", status_code=201)
def create_run(body: CreateRunRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = RunService(RunRepository(db))
    return service.create_run(
        project_id=body.project_id,
        connection_id=body.connection_id,
        dataset_id=body.dataset_id,
        started_by=body.started_by,
    )


@router.get("/{id}")
def get_run(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = RunService(RunRepository(db))
    run = service.get_run(id)
    if run is None:
        raise NotFoundError("Run not found")
    return run
