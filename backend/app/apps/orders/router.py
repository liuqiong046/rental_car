"""Customer order confirmation API routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Query, status

from app.apps.admin.deps import require_admin_actor
from app.apps.admin.schemas import AdminActor
from app.apps.orders.schemas import (
    CustomerOrderDetail,
    CustomerOrderListResponse,
    ExpireUnpaidOrdersResponse,
    FeeEstimate,
    OrderAcceptRequest,
    OrderCancelRequest,
    OrderConfirmRequest,
    OrderReassignRequest,
    OrderReturnRequest,
)
from app.apps.orders.service import customer_order_service
from app.apps.users.deps import require_current_customer
from app.apps.users.schemas import CustomerProfile

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/estimate",
    response_model=FeeEstimate,
    status_code=status.HTTP_200_OK,
    summary="预估确认订单费用",
)
async def estimate_order_fee(
    payload: OrderConfirmRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
) -> FeeEstimate:
    _ = customer
    return customer_order_service.estimate(payload)


@router.post(
    "",
    response_model=CustomerOrderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="创建待支付客户订单并锁车",
)
async def create_pending_payment_order(
    payload: OrderConfirmRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> CustomerOrderDetail:
    return customer_order_service.create_pending_payment_order(customer, payload, idempotency_key)


@router.post(
    "/{order_id}/cancel",
    response_model=CustomerOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="取消待支付客户订单并释放锁车",
)
async def cancel_pending_payment_order(
    order_id: str,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
    payload: Annotated[OrderCancelRequest | None, Body()] = None,
) -> CustomerOrderDetail:
    return customer_order_service.cancel_pending_payment_order(
        customer.user_id,
        order_id,
        payload or OrderCancelRequest(),
    )


@router.post(
    "/admin/expire-unpaid",
    response_model=ExpireUnpaidOrdersResponse,
    status_code=status.HTTP_200_OK,
    summary="执行未支付订单超时关闭并释放车辆",
)
async def expire_unpaid_orders(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    minutes_after_lock: Annotated[int | None, Query(ge=0)] = None,
) -> ExpireUnpaidOrdersResponse:
    _ = actor
    return customer_order_service.expire_unpaid_orders(minutes_after_lock)


@router.get(
    "/admin/customer-orders",
    response_model=CustomerOrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="查询客户订单列表",
)
async def list_admin_customer_orders(
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    order_status: Annotated[str | None, Query(alias="status")] = None,
) -> CustomerOrderListResponse:
    return customer_order_service.list_admin_customer_orders(actor.account_id, order_status)


@router.get(
    "/admin/customer-orders/{order_id}",
    response_model=CustomerOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="查询客户订单详情",
)
async def get_admin_customer_order(
    order_id: str,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
) -> CustomerOrderDetail:
    return customer_order_service.get_admin_customer_order(actor.account_id, order_id)


@router.post(
    "/admin/customer-orders/{order_id}/accept",
    response_model=CustomerOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="客户订单接单并进入待排车",
)
async def accept_customer_order(
    order_id: str,
    payload: OrderAcceptRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> CustomerOrderDetail:
    return customer_order_service.accept_customer_order(
        actor.account_id,
        order_id,
        payload,
        idempotency_key,
    )


@router.post(
    "/admin/customer-orders/{order_id}/return",
    response_model=CustomerOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="客户订单进入待退单",
)
async def return_customer_order(
    order_id: str,
    payload: OrderReturnRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> CustomerOrderDetail:
    return customer_order_service.return_customer_order(
        actor.account_id,
        order_id,
        payload,
        idempotency_key,
    )


@router.post(
    "/admin/customer-orders/{order_id}/reassign",
    response_model=CustomerOrderDetail,
    status_code=status.HTTP_200_OK,
    summary="客户订单改派同车型车辆",
)
async def reassign_customer_order(
    order_id: str,
    payload: OrderReassignRequest,
    actor: Annotated[AdminActor, Depends(require_admin_actor)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> CustomerOrderDetail:
    return customer_order_service.reassign_customer_order(
        actor.account_id,
        order_id,
        payload,
        idempotency_key,
    )
