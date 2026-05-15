from fastapi import APIRouter, Depends

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.errors import NotFoundError
from refresh.service import get_current_status, get_job, trigger_refresh

router = APIRouter(prefix="/api/refresh", tags=["refresh"])


@router.post("")
def request_refresh(
    current_user: SessionUser = Depends(get_current_user),
):
    return trigger_refresh(user_id=current_user.id)


@router.get("/current")
def refresh_current(
    current_user: SessionUser = Depends(get_current_user),
):
    return get_current_status()


@router.get("/jobs/{job_id}")
def refresh_job(
    job_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_job(job_id)
    if result is None:
        raise NotFoundError("Refresh job not found")
    return result
