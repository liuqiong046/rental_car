"""Payment API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.apps.payments.schemas import (
    PaymentCallbackResponse,
    PaymentPrepayRequest,
    PaymentPrepayResponse,
    WechatPaymentCallbackRequest,
)
from app.apps.payments.service import payment_service
from app.apps.users.deps import require_current_customer
from app.apps.users.schemas import CustomerProfile

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/prepay",
    response_model=PaymentPrepayResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建微信支付预下单",
)
async def create_wechat_prepay(
    payload: PaymentPrepayRequest,
    customer: Annotated[CustomerProfile, Depends(require_current_customer)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> PaymentPrepayResponse:
    return payment_service.create_wechat_prepay(customer, payload.order_id, idempotency_key)


@router.post(
    "/wechat/callback",
    response_model=PaymentCallbackResponse,
    status_code=status.HTTP_200_OK,
    summary="处理微信支付回调",
)
async def handle_wechat_payment_callback(
    payload: WechatPaymentCallbackRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8)],
) -> PaymentCallbackResponse:
    return payment_service.handle_wechat_callback(payload, idempotency_key)
