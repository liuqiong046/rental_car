"""Vehicle and price calendar API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.apps.admin.deps import require_admin_actor
from app.apps.admin.schemas import AdminActor
from app.apps.vehicles.schemas import (
    PriceCalendarBatchUpdateRequest,
    PriceCalendarEntry,
    PriceCalendarListResponse,
    PriceCalendarUpdateRequest,
    PublicVehicleDetail,
    PublicVehicleListResponse,
    VehicleCreateRequest,
    VehicleDetail,
    VehicleListResponse,
    VehicleModel,
    VehicleModelCreateRequest,
    VehicleModelListResponse,
    VehicleModelUpdateRequest,
    VehiclePublicSearch,
    VehicleStatusUpdateRequest,
    VehicleUpdateRequest,
)
from app.apps.vehicles.service import vehicle_inventory_service

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get(
    "",
    response_model=PublicVehicleListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询 C 端可租车辆列表",
)
async def list_public_vehicles(
    city_code: Annotated[str | None, Query()] = None,
    pickup_at: Annotated[str | None, Query()] = None,
    return_at: Annotated[str | None, Query()] = None,
    brand: Annotated[str | None, Query()] = None,
    price_min: Annotated[int | None, Query(ge=0)] = None,
    price_max: Annotated[int | None, Query(ge=0)] = None,
    color: Annotated[str | None, Query()] = None,
    vehicle_type: Annotated[str | None, Query()] = None,
    energy_type: Annotated[str | None, Query()] = None,
    seats: Annotated[int | None, Query(ge=1)] = None,
    gearbox: Annotated[str | None, Query()] = None,
) -> VehicleListResponse:
    filters = VehiclePublicSearch(
        city_code=city_code,
        pickup_at=pickup_at,
        return_at=return_at,
        brand=brand,
        price_min=price_min,
        price_max=price_max,
        color=color,
        vehicle_type=vehicle_type,
        energy_type=energy_type,
        seats=seats,
        gearbox=gearbox,
    )
    return vehicle_inventory_service.list_public_available(filters)


@router.get(
    "/{vehicle_id}",
    response_model=PublicVehicleDetail,
    status_code=status.HTTP_200_OK,
    summary="查询 C 端可租车辆详情",
)
async def read_public_vehicle(vehicle_id: str) -> VehicleDetail:
    return vehicle_inventory_service.get_public_vehicle(vehicle_id)


@router.get(
    "/admin/models",
    response_model=VehicleModelListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询后台车型库",
)
async def list_admin_vehicle_models(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleModelListResponse:
    return vehicle_inventory_service.list_models(actor)


@router.post(
    "/admin/models",
    response_model=VehicleModel,
    status_code=status.HTTP_201_CREATED,
    summary="新增后台车型",
)
async def create_admin_vehicle_model(
    payload: VehicleModelCreateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleModel:
    return vehicle_inventory_service.create_model(actor, payload)


@router.patch(
    "/admin/models/{model_id}",
    response_model=VehicleModel,
    status_code=status.HTTP_200_OK,
    summary="编辑后台车型",
)
async def update_admin_vehicle_model(
    model_id: str,
    payload: VehicleModelUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleModel:
    return vehicle_inventory_service.update_model(actor, model_id, payload)


@router.delete(
    "/admin/models/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除后台车型",
)
async def delete_admin_vehicle_model(
    model_id: str,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> None:
    vehicle_inventory_service.delete_model(actor, model_id)


@router.get(
    "/admin/items",
    response_model=VehicleListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询后台车辆列表",
)
async def list_admin_vehicles(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleListResponse:
    return vehicle_inventory_service.list_admin_vehicles(actor)


@router.post(
    "/admin/items",
    response_model=VehicleDetail,
    status_code=status.HTTP_201_CREATED,
    summary="新增后台车辆",
)
async def create_admin_vehicle(
    payload: VehicleCreateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleDetail:
    return vehicle_inventory_service.create_vehicle(actor, payload)


@router.patch(
    "/admin/items/{vehicle_id}",
    response_model=VehicleDetail,
    status_code=status.HTTP_200_OK,
    summary="编辑后台车辆",
)
async def update_admin_vehicle(
    vehicle_id: str,
    payload: VehicleUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleDetail:
    return vehicle_inventory_service.update_vehicle(actor, vehicle_id, payload)


@router.delete(
    "/admin/items/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除后台车辆",
)
async def delete_admin_vehicle(
    vehicle_id: str,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> None:
    vehicle_inventory_service.delete_vehicle(actor, vehicle_id)


@router.patch(
    "/admin/items/{vehicle_id}/status",
    response_model=VehicleDetail,
    status_code=status.HTTP_200_OK,
    summary="更新后台车辆审核、上下架、维保或锁车状态",
)
async def update_vehicle_status(
    vehicle_id: str,
    payload: VehicleStatusUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> VehicleDetail:
    return vehicle_inventory_service.update_vehicle_status(actor, vehicle_id, payload)


@router.get(
    "/admin/items/{vehicle_id}/prices",
    response_model=PriceCalendarListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询后台车辆价格日历",
)
async def list_vehicle_prices(
    vehicle_id: str,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> dict[str, object]:
    return vehicle_inventory_service.list_price_calendar(actor, vehicle_id)


@router.put(
    "/admin/items/{vehicle_id}/prices",
    response_model=PriceCalendarEntry,
    status_code=status.HTTP_200_OK,
    summary="维护后台车辆价格日历",
)
async def upsert_vehicle_price(
    vehicle_id: str,
    payload: PriceCalendarUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> PriceCalendarEntry:
    return vehicle_inventory_service.upsert_price(actor, vehicle_id, payload)


@router.put(
    "/admin/items/{vehicle_id}/prices/batch",
    response_model=PriceCalendarListResponse,
    status_code=status.HTTP_200_OK,
    summary="批量维护后台车辆价格日历",
)
async def upsert_vehicle_prices_batch(
    vehicle_id: str,
    payload: PriceCalendarBatchUpdateRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> dict[str, object]:
    return vehicle_inventory_service.upsert_prices_batch(actor, vehicle_id, payload)
