from fastapi import APIRouter, Depends

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.exports import ExportRequest
from exports.service import request_export

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.post("/executive-summary")
def export_executive_summary(
    body: ExportRequest,
    current_user: SessionUser = Depends(get_current_user),
):
    return request_export(body)
