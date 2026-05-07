"""In-memory payment orchestration service."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status

from app.apps.orders.schemas import CustomerOrderDetail
from app.apps.orders.service import customer_order_service
from app.apps.payments.schemas import (
    PaymentCallbackResponse,
    PaymentPrepayResponse,
    PaymentRecord,
    WechatPaymentCallbackRequest,
)
from app.apps.users.schemas import CustomerProfile
from app.core.config import settings
from app.integrations.wechat.payments import build_mock_wechat_pay_params


class PaymentService:
    def __init__(self) -> None:
        # TODO(WF-P0-10): 支付流水、幂等键和微信交易号当前为内存实现；
        # 正式接入微信支付时需落库并按回调验签结果记录审计日志。
        self.payments: dict[str, PaymentRecord] = {}
        self.prepay_idempotency_index: dict[str, str] = {}
        self.callback_idempotency_index: dict[str, PaymentCallbackResponse] = {}
        self.order_payment_index: dict[str, str] = {}
        self.success_transaction_index: dict[str, str] = {}

    def create_wechat_prepay(
        self,
        customer: CustomerProfile,
        order_id: str,
        idempotency_key: str,
    ) -> PaymentPrepayResponse:
        indexed_key = f"{customer.user_id}:payments/prepay:{idempotency_key}"
        if indexed_key in self.prepay_idempotency_index:
            payment_id = self.prepay_idempotency_index[indexed_key]
            return self._response_from_record(self.payments[payment_id])

        order = customer_order_service.get_order_for_payment(order_id, customer.user_id)
        existing_payment_id = self.order_payment_index.get(order_id)
        if existing_payment_id is not None:
            self.prepay_idempotency_index[indexed_key] = existing_payment_id
            return self._response_from_record(self.payments[existing_payment_id])

        payment_id = f"pay_{uuid4().hex[:12]}"
        record = PaymentRecord(
            payment_id=payment_id,
            order_id=order.order_id,
            user_id=customer.user_id,
            provider="wechat_mock",
            payable_amount=order.payable_amount,
            status="prepay_created",
            pay_params=build_mock_wechat_pay_params(payment_id),
            mock_callback_url=f"{settings.api_v1_prefix}/payments/wechat/callback",
            created_at=_now_iso(),
        )
        self.payments[payment_id] = record
        self.order_payment_index[order_id] = payment_id
        self.prepay_idempotency_index[indexed_key] = payment_id
        return self._response_from_record(record)

    def handle_wechat_callback(
        self,
        payload: WechatPaymentCallbackRequest,
        idempotency_key: str,
    ) -> PaymentCallbackResponse:
        indexed_key = f"wechat_callback:{idempotency_key}"
        if indexed_key in self.callback_idempotency_index:
            return self.callback_idempotency_index[indexed_key]

        record = self._get_payment(payload.payment_id, payload.order_id)
        response = self._handle_callback_payload(record, payload)
        self.callback_idempotency_index[indexed_key] = response
        return response

    def _handle_callback_payload(
        self,
        record: PaymentRecord,
        payload: WechatPaymentCallbackRequest,
    ) -> PaymentCallbackResponse:
        order = customer_order_service.get_order_for_payment_callback(payload.order_id)
        if payload.trade_state != "SUCCESS":
            updated_record = record.model_copy(update={"status": _failed_status(payload.trade_state)})
            self.payments[record.payment_id] = updated_record
            return _callback_response(updated_record, order, True)

        if payload.transaction_id in self.success_transaction_index or record.status == "paid":
            paid_order = customer_order_service.get_order_for_payment_callback(payload.order_id)
            return _callback_response(record, paid_order, False)
        if payload.paid_amount != record.payable_amount or payload.paid_amount != order.payable_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="支付金额不一致")

        paid_order = customer_order_service.mark_paid_after_callback(payload.order_id)
        updated_record = record.model_copy(
            update={"status": "paid", "transaction_id": payload.transaction_id},
        )
        self.payments[record.payment_id] = updated_record
        self.success_transaction_index[payload.transaction_id] = record.payment_id
        return _callback_response(updated_record, paid_order, True)

    def _get_payment(self, payment_id: str, order_id: str) -> PaymentRecord:
        record = self.payments.get(payment_id)
        if record is None or record.order_id != order_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="支付流水不存在")
        return record

    def _response_from_record(self, record: PaymentRecord) -> PaymentPrepayResponse:
        return PaymentPrepayResponse(
            payment_id=record.payment_id,
            order_id=record.order_id,
            provider=record.provider,
            payable_amount=record.payable_amount,
            status=record.status,
            pay_params=record.pay_params,
            mock_callback_url=record.mock_callback_url,
            created_at=record.created_at,
        )


def _callback_response(
    record: PaymentRecord,
    order: CustomerOrderDetail,
    processed: bool,
) -> PaymentCallbackResponse:
    return PaymentCallbackResponse(
        payment_id=record.payment_id,
        order_id=record.order_id,
        transaction_id=record.transaction_id,
        processed=processed,
        payment_status=order.payment_status,
        order_status=order.order_status,
    )


def _failed_status(trade_state: str) -> str:
    if trade_state == "CANCEL":
        return "cancelled"
    return "failed"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


payment_service = PaymentService()
