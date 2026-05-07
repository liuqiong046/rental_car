"""System health routes."""

from fastapi import APIRouter, status

from app.apps.system.schemas import HealthCheckResponse
from app.apps.system.service import get_health_check

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="查询 API 健康状态",
)
async def read_system_health() -> HealthCheckResponse:
    return get_health_check()

