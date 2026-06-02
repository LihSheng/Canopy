from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from context.authorization import verify_tenant_ownership
from context.tenant_context import TenantContext
from project.repository import ProjectRepository
from project.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


def _build_service(db: Session) -> ProjectService:
    return ProjectService(ProjectRepository(db))


@router.get("/")
def list_projects(
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.list_projects(tenant_id=ctx.tenant_id)


@router.post("/", status_code=201)
def create_project(
    body: CreateProjectRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.create_project(tenant_id=ctx.tenant_id, name=body.name, description=body.description)


@router.get("/{id}")
def get_project(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    project = service.get_project(id, tenant_id=ctx.tenant_id)
    if project is None:
        raise NotFoundError("Project not found")
    # Cross-check ownership at route level for defense in depth
    verify_tenant_ownership(ctx, project.tenant_id, "Project")
    return project
