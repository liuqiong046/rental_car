"""System service helpers."""

from app.apps.system.schemas import HealthCheckResponse
from app.core.config import settings


def get_health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="ok",
        service=settings.service_name,
        version=settings.app_version,
    )

