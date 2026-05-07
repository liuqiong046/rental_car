"""City, homepage, and service rule API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.apps.admin.deps import require_admin_actor
from app.apps.admin.schemas import AdminActor
from app.apps.cities.schemas import (
    CityConfig,
    CityConfigCreateRequest,
    CityConfigListResponse,
    CityConfigUpdateRequest,
)
from app.apps.cities.service import city_config_service

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get(
    "",
    response_model=CityConfigListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询 C 端可用城市配置",
)
async def list_public_cities() -> CityConfigListResponse:
    return city_config_service.list_public_cities()


@router.get(
    "/{city_code}",
    response_model=CityConfig,
    status_code=status.HTTP_200_OK,
    summary="查询 C 端城市有效规则",
)
async def read_public_city(city_code: str) -> CityConfig:
    return city_config_service.get_public_city(city_code)


@router.get(
    "/admin/configs",
    response_model=CityConfigListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询后台城市规则配置",
)
async def list_admin_city_configs(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> CityConfigListResponse:
    return city_config_service.list_admin_cities(actor)


@router.post(
    "/admin/configs",
    response_model=CityConfig,
    status_code=status.HTTP_201_CREATED,
    summary="新增后台城市规则配置",
)
async def create_admin_city_config(
    payload: CityConfigCreateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> CityConfig:
    return city_config_service.create_city(actor, payload)


@router.patch(
    "/admin/configs/{city_code}",
    response_model=CityConfig,
    status_code=status.HTTP_200_OK,
    summary="更新后台城市规则配置",
)
async def update_admin_city_config(
    city_code: str,
    payload: CityConfigUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> CityConfig:
    return city_config_service.update_city(actor, city_code, payload)
