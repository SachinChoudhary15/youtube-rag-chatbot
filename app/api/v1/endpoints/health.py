

from fastapi import APIRouter
from app.schemas.common import HealthCheckResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    return HealthCheckResponse(status="healthy")