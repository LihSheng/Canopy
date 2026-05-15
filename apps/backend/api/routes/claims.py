from fastapi import APIRouter, Depends, Query

from analytics.departments import get_claims
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.get("")
def list_claims(
    department_id: str | None = Query(default=None),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_claims(department_id=department_id)
