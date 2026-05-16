from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics.departments import (
    get_claims,
    get_department,
    get_department_claim_types,
    get_department_employees,
    get_department_trends,
)
from analytics.departments import (
    get_departments as get_all_departments,
)
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.departments import (
    DepartmentDetailResponse,
)
from common.database import get_db
from common.errors import NotFoundError

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("")
def list_departments(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    sort_by: str | None = Query(default=None, description="Sort: total_spend, change_pct, attention"),
):
    return get_all_departments(db, sort_by=sort_by)


@router.get("/{department_id}", response_model=DepartmentDetailResponse)
def department_detail(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_department(db, department_id)
    if result is None:
        raise NotFoundError("Department not found")
    return result


@router.get("/{department_id}/trends")
def department_trends(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_department_trends(db, department_id)


@router.get("/{department_id}/employees")
def department_employees(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_department_employees(db, department_id)


@router.get("/{department_id}/claim-types")
def department_claim_types(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_department_claim_types(db, department_id)


@router.get("/{department_id}/claims")
def department_claims(
    department_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_claims(db, department_id=department_id)
