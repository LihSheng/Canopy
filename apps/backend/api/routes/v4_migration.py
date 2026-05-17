from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from v4.migration.service import MigrationService

router = APIRouter(prefix="/api/migration", tags=["migration"])


@router.get("/uploads")
def list_migratable_uploads(db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = MigrationService(db)
    return service.list_migratable_uploads()


@router.get("/uploads/{upload_id}/mapping")
def get_upload_mapping(upload_id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = MigrationService(db)
    connection = service.map_upload_to_connection(upload_id)
    datasets = service.map_upload_to_datasets(upload_id)
    runs = service.map_workflow_to_runs(upload_id)
    lineage = service.get_v4_lineage(upload_id)
    return {
        "connection": connection,
        "datasets": datasets,
        "runs": runs,
        "lineage": lineage,
    }
