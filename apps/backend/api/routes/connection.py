from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError, ValidationError
from v4.connection.repository import ConnectionRepository
from v4.connection.importer import build_sheet_profiles, save_uploaded_file
from v4.connection.service import ConnectionService

router = APIRouter(prefix="/connections", tags=["connections"])


class CreateConnectionRequest(BaseModel):
    project_id: str
    source_type: str
    name: str
    config_json: dict = Field(default_factory=dict)


class SheetProfileResponse(BaseModel):
    sheet_name: str
    row_count: int
    column_count: int
    header_row_index: int | None
    confidence: float
    warnings: list[str]


class StaticFilePreviewResponse(BaseModel):
    source_file_path: str
    file_name: str
    sheet_profiles: list[SheetProfileResponse]


@router.get("/")
def list_connections(project_id: str = Query(""), db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ConnectionService(ConnectionRepository(db))
    if project_id:
        return service.list_connections(project_id)
    return service.list_all_connections()


@router.post("/", status_code=201)
def create_connection(body: CreateConnectionRequest, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ConnectionService(ConnectionRepository(db))
    return service.create_connection(
        project_id=body.project_id,
        source_type=body.source_type,
        name=body.name,
        config_json=body.config_json,
    )


@router.post("/preview")
def preview_static_file(
    file: UploadFile = File(...),
    source_type: str = Form("static_file"),
    db: Session = Depends(get_db),
    user: SessionUser = Depends(get_current_user),
):
    if source_type != "static_file":
        raise ValidationError("Only static_file preview is supported")

    storage_path = save_uploaded_file(file)
    sheet_profiles = build_sheet_profiles(storage_path)
    return StaticFilePreviewResponse(
        source_file_path=str(storage_path),
        file_name=file.filename or storage_path.name,
        sheet_profiles=[SheetProfileResponse(**profile) for profile in sheet_profiles],
    )


@router.get("/{id}")
def get_connection(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ConnectionService(ConnectionRepository(db))
    connection = service.get_connection(id)
    if connection is None:
        raise NotFoundError("Connection not found")
    return connection
