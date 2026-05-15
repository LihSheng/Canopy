from fastapi import APIRouter, Depends

from anomalies.service import get_anomalies, get_anomaly
from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.errors import NotFoundError

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("")
def list_anomalies(
    current_user: SessionUser = Depends(get_current_user),
):
    return get_anomalies()


@router.get("/{anomaly_id}")
def anomaly_detail(
    anomaly_id: str,
    current_user: SessionUser = Depends(get_current_user),
):
    result = get_anomaly(anomaly_id)
    if result is None:
        raise NotFoundError("Anomaly not found")
    return result
