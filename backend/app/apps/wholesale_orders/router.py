"""Wholesale order API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, status

from app.apps.admin.deps import require_admin_actor
from app.apps.admin.schemas import AdminActor
from app.apps.wholesale_orders.schemas import (
    ExpireWholesaleOrdersResponse,
    WholesaleOrderAcceptRequest,
    WholesaleOrderChangePriceRequest,
    WholesaleOrderCreateRelatedRequest,
    WholesaleOrderDetail,
    WholesaleOrderListResponse,
    WholesaleOrderRejectRequest,
)
from app.apps.wholesale_orders.service import wholesale_order_service

router = APIRouter(prefix="/wholesale-orders", tags=["wholesale-orders"])


@router.get(
    "",
    response_model=WholesaleOrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询批发订单列表",
)
async def list_wholesale_orders(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    order_status: Annotated[str | None, Query(alias="status")] = None,
) -> WholesaleOrderListResponse:
    return wholesale_order_service.list_orders(actor, order_status)


@router.post(
    "/admin/related",
    response_model=WholesaleOrderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="为车行客户订单创建关联批发订单",
)
async def create_related_wholesale_order(
    payload: WholesaleOrderCreateRelatedRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> WholesaleOrderDetail:
    return wholesale_order_service.create_related_order(actor, payload, idempotency_key)


@router.post(
    "/admin/expire-pending",
    response_model=ExpireWholesaleOrdersResponse,
    status_code=status.HTTP_200_OK,
    summary="执行批发订单确认 SLA 超时拒绝",
)
async def expire_pending_wholesale_orders(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    minutes_after_sla: Annotated[int | None, Query(ge=0)] = None,
) -> ExpireWholesaleOrdersResponse:
    return wholesale_order_service.expire_pending_orders(actor, minutes_after_sla)


@router.post(
    "/{wholesale_order_id}/accept",
    response_model=WholesaleOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="车行接单批发订单",
)
async def accept_wholesale_order(
    wholesale_order_id: str,
    payload: WholesaleOrderAcceptRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> WholesaleOrderDetail:
    return wholesale_order_service.accept_order(actor, wholesale_order_id, payload.remark, idempotency_key)


@router.post(
    "/{wholesale_order_id}/reject",
    response_model=WholesaleOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="车行拒绝批发订单",
)
async def reject_wholesale_order(
    wholesale_order_id: str,
    payload: WholesaleOrderRejectRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> WholesaleOrderDetail:
    return wholesale_order_service.reject_order(actor, wholesale_order_id, payload.reason, idempotency_key)


@router.post(
    "/{wholesale_order_id}/change-price",
    response_model=WholesaleOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="车行修改批发订单价格",
)
async def change_wholesale_order_price(
    wholesale_order_id: str,
    payload: WholesaleOrderChangePriceRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> WholesaleOrderDetail:
    return wholesale_order_service.change_price(actor, wholesale_order_id, payload, idempotency_key)
