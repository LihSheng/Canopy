from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics.departments import get_claims
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.get("")
def list_claims(
    db: Session = Depends(get_db),
    department_id: str | None = Query(default=None),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_claims(db, department_id=department_id)
