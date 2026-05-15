from fastapi import APIRouter

from api.schemas.health import HealthResponse
from common.clock import iso_now

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=iso_now())
