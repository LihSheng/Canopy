from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.exports import ExportRequest
from common.database import session_factory
from exports.service import generate_export

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.post("/executive-summary")
def export_executive_summary(
    body: ExportRequest,
    current_user: SessionUser = Depends(get_current_user),
):
    db = session_factory()()
    try:
        excel_bytes = generate_export(
            db=db,
            include_departments=body.include_departments,
            include_anomalies=body.include_anomalies,
        )
    finally:
        db.close()

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=executive-summary.xlsx"
        },
    )
