from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from common.errors import NotFoundError
from v4.connection.repository import ConnectionRepository
from v4.connection.service import ConnectionService

router = APIRouter(prefix="/api/connections", tags=["connections"])


class CreateConnectionRequest(BaseModel):
    project_id: str
    source_type: str
    name: str
    config_json: dict = {}


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


@router.get("/{id}")
def get_connection(id: str, db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    service = ConnectionService(ConnectionRepository(db))
    connection = service.get_connection(id)
    if connection is None:
        raise NotFoundError("Connection not found")
    return connection
