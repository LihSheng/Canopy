"""Admin-only feature flag management routes.

GET /api/feature-flags           — read enabled flags map (authenticated users)
GET /api/admin/feature-flags     — list all flags (admin only)
PUT /api/admin/feature-flags/{flag_key} — toggle a flag (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import AuthError
from feature_flags.repository import FeatureFlagRepository
from feature_flags.service import FeatureFlagService

# Public read router (authenticated)
public_router = APIRouter(prefix="/api", tags=["feature-flags"])

# Admin management router
admin_router = APIRouter(prefix="/api/admin", tags=["admin-feature-flags"])


def _require_admin(current_user: SessionUser) -> None:
    if not current_user.is_admin:
        raise AuthError("Admin access required")


class ToggleFlagRequest(BaseModel):
    enabled: bool


# ─── Public endpoints ──────────────────────────────────────────────


@public_router.get("/feature-flags")
def get_enabled_flags(
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a map of flag_key -> enabled for use by the frontend context."""
    repo = FeatureFlagRepository(db)
    svc = FeatureFlagService(repo)
    svc.seed_defaults()
    return svc.get_enabled_map()


# ─── Admin endpoints ───────────────────────────────────────────────


@admin_router.get("/feature-flags")
def list_feature_flags(
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    repo = FeatureFlagRepository(db)
    svc = FeatureFlagService(repo)
    svc.seed_defaults()
    return svc.get_all()


@admin_router.put("/feature-flags/{flag_key}")
def toggle_feature_flag(
    flag_key: str,
    body: ToggleFlagRequest,
    current_user: SessionUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_admin(current_user)
    repo = FeatureFlagRepository(db)
    svc = FeatureFlagService(repo)
    svc.seed_defaults()
    result = svc.set_flag(flag_key, body.enabled)
    if not result:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_key}' not found")
    return result
