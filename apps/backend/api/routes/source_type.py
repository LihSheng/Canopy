from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from common.database import get_db
from source_type.repository import SourceTypeRepository
from source_type.service import SourceTypeService

router = APIRouter(prefix="/source-types", tags=["source_types"])


@router.get("/")
def list_source_types(db: Session = Depends(get_db), user: SessionUser = Depends(get_current_user)):
    repo = SourceTypeRepository(db)
    service = SourceTypeService(repo)
    service.ensure_seeded()
    return service.list_source_types()

