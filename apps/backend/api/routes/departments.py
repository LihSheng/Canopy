from fastapi import APIRouter, Depends, Query

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
from common.errors import NotFoundError

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("")
def list_departments(
    current_user: SessionUser = Depends(get_current_user),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    return get_all_departments()


@router.get("/{department_id}")
def department_detail(
    department_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_department(department_id)
    if result is None:
        raise NotFoundError("Department not found")
    return result


@router.get("/{department_id}/trends")
def department_trends(
    department_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    return get_department_trends(department_id)


@router.get("/{department_id}/employees")
def department_employees(
    department_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    return get_department_employees(department_id)


@router.get("/{department_id}/claim-types")
def department_claim_types(
    department_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    return get_department_claim_types(department_id)


@router.get("/{department_id}/claims")
def department_claims(
    department_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    return get_claims(department_id=department_id)
