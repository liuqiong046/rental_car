"""FastAPI application entrypoint for rental_car."""

from fastapi import FastAPI, status

from app.api import api_router
from app.apps.system.schemas import HealthCheckResponse
from app.apps.system.service import get_health_check
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import request_id_middleware
from app.core.middleware import REQUEST_ID_HEADER


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="山海放心租 API",
        version=settings.app_version,
        description=(
            "Rental car API baseline. Business modules are added by WF-P0 tasks. "
            "Interface contract: doc/接口规范-V1.md"
        ),
    )

    app.middleware("http")(request_id_middleware)
    app.include_router(api_router)

    @app.get(
        "/healthz",
        response_model=HealthCheckResponse,
        status_code=status.HTTP_200_OK,
        summary="健康检查",
    )
    async def healthz() -> HealthCheckResponse:
        return get_health_check()

    return app


app = create_app()
