from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from analytics.service import (
    get_claim_type_breakdown,
    get_dashboard_summary,
    get_monthly_trends,
    get_top_departments,
)
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_dashboard_summary(db)


@router.get("/trends")
def dashboard_trends(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
):
    return get_monthly_trends(db, year=year, month=month)


@router.get("/top-departments")
def dashboard_top_departments(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_top_departments(db)


@router.get("/claim-types")
def dashboard_claim_types(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_claim_type_breakdown(db)
