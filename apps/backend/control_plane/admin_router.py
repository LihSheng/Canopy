from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from auth.repository import AuthRepository
from common.config import settings
from common.database import get_db
from common.errors import AuthError, ValidationError
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.lifecycle_service import LifecycleService
from control_plane.provisioning_service import ProvisioningService
from control_plane.tenant_repository import TenantRepository

router = APIRouter(prefix="/api/admin", tags=["admin"])

_ALGORITHM = "HS256"
_IMPERSONATION_EXPIRY_MINUTES = 60


def _require_admin(current_user: SessionUser, db: Session = Depends(get_db)):
    repo = AuthRepository(db)
    user = repo.find_by_id(current_user.id)
    if user is None or not user.is_admin:
        raise AuthError("Admin access required")


class CreateTenantRequest(BaseModel):
    name: str
    slug: str


class ImpersonateRequest(BaseModel):
    reason: str


@router.get("/tenants")
def list_tenants(
    status: str | None = None,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    repo = TenantRepository(db)
    tenants = repo.list_tenants(status_filter=status)
    return [
        {
            "id": t.id,
            "tenant_uuid": t.tenant_uuid,
            "name": t.name,
            "slug": t.slug,
            "lifecycle_state": t.lifecycle_state,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}")
def get_tenant(
    tenant_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    repo = TenantRepository(db)
    tenant = repo.get_tenant_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "id": tenant.id,
        "tenant_uuid": tenant.tenant_uuid,
        "name": tenant.name,
        "slug": tenant.slug,
        "lifecycle_state": tenant.lifecycle_state,
        "status": tenant.status,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None,
    }


@router.post("/tenants")
def create_tenant(
    body: CreateTenantRequest,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    repo = TenantRepository(db)
    existing = repo.get_tenant_by_slug(body.slug)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")
    tenant = repo.create_tenant(name=body.name, slug=body.slug)
    return {
        "id": tenant.id,
        "tenant_uuid": tenant.tenant_uuid,
        "name": tenant.name,
        "slug": tenant.slug,
        "lifecycle_state": tenant.lifecycle_state,
        "status": tenant.status,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
    }


@router.post("/tenants/{tenant_id}/provision")
def provision_tenant(
    tenant_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    service = ProvisioningService(db)
    try:
        job = service.provision_tenant(tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "job_id": job.id,
        "tenant_id": job.tenant_id,
        "job_type": job.job_type,
        "status": job.status,
    }


@router.post("/tenants/{tenant_id}/suspend")
def suspend_tenant(
    tenant_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    service = LifecycleService(db)
    try:
        tenant = service.suspend_tenant(tenant_id, current_user.id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "lifecycle_state": tenant.lifecycle_state,
    }


@router.post("/tenants/{tenant_id}/restore")
def restore_tenant(
    tenant_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    service = LifecycleService(db)
    try:
        tenant = service.restore_tenant(tenant_id, current_user.id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "lifecycle_state": tenant.lifecycle_state,
    }


@router.post("/tenants/{tenant_id}/archive")
def archive_tenant(
    tenant_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    service = LifecycleService(db)
    try:
        tenant = service.archive_tenant(tenant_id, current_user.id)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "lifecycle_state": tenant.lifecycle_state,
    }


@router.post("/tenants/{tenant_id}/impersonate")
def impersonate_tenant(
    tenant_id: str,
    body: ImpersonateRequest,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    audit = AuditService(db)
    tenant_repo = TenantRepository(db)
    tenant = tenant_repo.get_tenant_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    session = audit.record_impersonation_start(
        admin_user_id=current_user.id,
        tenant_id=tenant_id,
        reason=body.reason,
    )
    audit.record_event(
        tenant_id=tenant_id,
        actor_user_id=current_user.id,
        event_type="impersonation.started",
        payload={
            "admin_user_id": current_user.id,
            "tenant_id": tenant_id,
            "reason": body.reason,
            "session_id": session.id,
        },
    )

    expires_at = datetime.now(UTC) + timedelta(minutes=_IMPERSONATION_EXPIRY_MINUTES)
    token_payload = {
        "sub": current_user.id,
        "tenant_id": tenant_id,
        "impersonated": True,
        "admin_id": current_user.id,
        "impersonation_session_id": session.id,
        "exp": expires_at,
    }
    token = jwt.encode(token_payload, settings.secret_key, algorithm=_ALGORITHM)

    return {
        "token": token,
        "expires_at": expires_at.isoformat(),
        "tenant_id": tenant_id,
        "session_id": session.id,
    }


@router.get("/audit-events")
def list_audit_events(
    tenant_id: str | None = None,
    limit: int = 100,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    audit = AuditService(db)
    events = audit.get_audit_events(tenant_id=tenant_id, limit=limit)
    return [
        {
            "id": e.id,
            "tenant_id": e.tenant_id,
            "actor_user_id": e.actor_user_id,
            "event_type": e.event_type,
            "event_payload_json": e.event_payload_json,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/jobs")
def list_jobs(
    tenant_id: str | None = None,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    service = ProvisioningService(db)
    jobs = service.list_provisioning_jobs(tenant_id=tenant_id)
    return [
        {
            "id": j.id,
            "tenant_id": j.tenant_id,
            "job_type": j.job_type,
            "status": j.status,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
            "error_message": j.error_message,
            "attempt_count": j.attempt_count,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.get("/tenant-config/{tenant_id}")
def get_tenant_config(
    tenant_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user, db)
    repo = ConfigRepository(db)
    configs = repo.get_all_configs(tenant_id)
    return [
        {
            "id": c.id,
            "tenant_id": c.tenant_id,
            "config_key": c.config_key,
            "config_value_json": c.config_value_json,
            "version_number": c.version_number,
        }
        for c in configs
    ]

