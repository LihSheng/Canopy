from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user, require_tenant_context
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from context.authorization import verify_tenant_ownership
from context.tenant_context import TenantContext
from run.repository import RunRepository
from run.service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


class CreateRunRequest(BaseModel):
    project_id: str
    connection_id: str
    dataset_id: str
    started_by: str = ""


def _build_service(db: Session) -> RunService:
    return RunService(RunRepository(db))


@router.get("/")
def list_runs(
    project_id: str = Query(""),
    dataset_id: str = Query(""),
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    if dataset_id:
        return service.list_runs_by_dataset(dataset_id, tenant_id=ctx.tenant_id)
    if project_id:
        return service.list_runs_by_project(project_id, tenant_id=ctx.tenant_id)
    return service.list_all_runs(tenant_id=ctx.tenant_id)


@router.post("/", status_code=201)
def create_run(
    body: CreateRunRequest,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    return service.create_run(
        tenant_id=ctx.tenant_id,
        project_id=body.project_id,
        connection_id=body.connection_id,
        dataset_id=body.dataset_id,
        started_by=body.started_by,
    )


@router.get("/{id}")
def get_run(
    id: str,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    service = _build_service(db)
    run = service.get_run(id, tenant_id=ctx.tenant_id)
    if run is None:
        raise NotFoundError("Run not found")
    verify_tenant_ownership(ctx, run.tenant_id, "Run")
    return run
