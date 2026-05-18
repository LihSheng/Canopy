from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics.departments import get_claims
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.departments import ClaimDetailItem
from common.database import get_db

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.get("")
def list_claims(
    db: Session = Depends(get_db),
    department_id: str | None = Query(default=None),
    current_user: SessionUser = Depends(get_current_user),
):
    claims = get_claims(db, department_id=department_id)
    return [
        ClaimDetailItem(
            id=c.id,
            employee_name=c.employee_name,
            department=c.department,
            type=c.type,
            amount=c.amount,
            date=c.date,
        )
        for c in claims
    ]
