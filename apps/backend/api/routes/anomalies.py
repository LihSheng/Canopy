from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from anomalies.service import get_anomalies_list, get_anomaly_detail
from api.dependencies.auth import get_current_user
from api.schemas.anomalies import AnomalyDetailResponse, AnomalyItem
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
    department_id: str | None = Query(default=None, description="Filter by department"),
    time_range: str | None = Query(default=None, description="Time range filter (e.g. this_month)"),
):
    items = get_anomalies_list(db, department_id=department_id)
    return [AnomalyItem(**a) for a in items]


@router.get("/{anomaly_id}", response_model=AnomalyDetailResponse)
def anomaly_detail(
    anomaly_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_anomaly_detail(db, anomaly_id)
    if result is None:
        raise NotFoundError("Anomaly not found")
    return AnomalyDetailResponse(**result)
