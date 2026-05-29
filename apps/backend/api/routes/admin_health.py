"""Admin-only health dashboard routes.

All endpoints require admin authentication.
Mounted at /api/admin/health in app.py.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import AuthError
from health.service import RollupService

router = APIRouter(prefix="/health", tags=["admin-health"])


def _require_admin(current_user: SessionUser) -> None:
    if not current_user.is_admin:
        raise AuthError("Admin access required")


@router.get("/summary")
def health_summary(
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    summary = service.get_summary(tenant_id)
    failures = service.get_recent_failures(tenant_id, limit=10)
    return {
        "bytes_written_30d": summary["total_bytes_written"],
        "error_count_30d": summary["total_failures"],
        "warning_count_30d": summary["total_warnings"],
        "sla_violation_count_30d": summary["total_sla_violations"],
        "total_runs_30d": summary["total_runs"],
        "active_pipeline_count": summary["active_pipeline_count"],
        "recent_failures": failures,
    }


@router.get("/trends")
def health_trends(
    days: int = 30,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    return service.get_trends(tenant_id, window_days=days)


@router.get("/pipelines")
def pipeline_catalog(
    health_filter: str | None = None,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    catalog = service.get_pipeline_catalog(tenant_id)
    if health_filter:
        catalog = [p for p in catalog if p["health"] == health_filter]
    return catalog


@router.get("/pipelines/{pipeline_id}")
def pipeline_detail(
    pipeline_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    detail = service.get_pipeline_detail(tenant_id, pipeline_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    detail["recent_runs"] = service.get_recent_pipeline_runs(tenant_id, pipeline_id, limit=20)
    return detail


@router.get("/runs/{run_id}")
def run_detail(
    run_id: str,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    telemetry = service.get_run_telemetry(tenant_id, run_id)
    if not telemetry:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run_id,
        "steps": telemetry,
    }


@router.post("/refresh")
def refresh_rollups(
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Recompute rollups for today and yesterday (UTC) for the active tenant."""
    _require_admin(current_user)
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    utc_today = datetime.now(UTC).date()
    service.compute_daily_rollup(tenant_id, utc_today)
    service.compute_daily_rollup(tenant_id, utc_today - timedelta(days=1))
    return {"refreshed": True, "date": utc_today.isoformat()}


@router.post("/backfill")
def backfill_rollups(
    days: int = 30,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Operator-triggered backfill for the last N days (UTC)."""
    _require_admin(current_user)
    if days < 1 or days > 120:
        raise HTTPException(status_code=400, detail="days must be between 1 and 120")
    tenant_id = _resolve_tenant_id(current_user, db)
    service = RollupService(db)
    service.backfill(tenant_id, days=days)
    return {"backfilled": True, "days": days}


def _resolve_tenant_id(current_user: SessionUser, db: Session) -> str:
    """Resolve the effective tenant_id from request context or user state."""
    from context.tenant_context import get_current_tenant_context

    ctx = get_current_tenant_context()
    if ctx and ctx.tenant_id:
        return ctx.tenant_id
    # Fallback: get user's first active tenant
    from control_plane.schemas.memberships import TenantMembershipModel

    membership = (
        db.query(TenantMembershipModel)
        .filter(
            TenantMembershipModel.user_id == current_user.id,
            TenantMembershipModel.status == "active",
        )
        .first()
    )
    if membership:
        return membership.tenant_id
    raise HTTPException(status_code=400, detail="No tenant context available")
