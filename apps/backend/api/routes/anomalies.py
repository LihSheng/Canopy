from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from anomalies.service import get_anomalies_list, get_anomaly_detail
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    return get_anomalies_list(db)


@router.get("/{anomaly_id}")
def anomaly_detail(
    anomaly_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_anomaly_detail(db, anomaly_id)
    if result is None:
        raise NotFoundError("Anomaly not found")
    return result
