from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from v4.project.repository import ProjectRepository
from v4.project.service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


@router.get("/")
def list_projects(db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    return service.list_projects()


@router.post("/", status_code=201)
def create_project(body: CreateProjectRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    return service.create_project(name=body.name, description=body.description)


@router.get("/{id}")
def get_project(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ProjectService(ProjectRepository(db))
    project = service.get_project(id)
    if project is None:
        raise NotFoundError("Project not found")
    return project
