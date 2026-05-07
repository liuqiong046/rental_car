"""DTOs for customer order confirmation and unpaid locks."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PickupMode = Literal["self_pickup", "delivery"]
ReturnMode = Literal["self_return", "pickup"]
OrderStatus = Literal[
    "pending_payment",
    "pending_acceptance",
    "pending_dispatch",
    "pending_reassign",
    "pending_return",
    "closed",
]
# TODO(WF-P0-12/WF-P0-18): H5/PRD 订单中心还需要批发关联、待取车、租赁中、
# 待还车、售后中、待结算、已完成、退款状态、押金状态和续租/提前还车状态。
PaymentStatus = Literal["unpaid", "paid"]


class OrderConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: str
    city_code: str
    pickup_at: str
    return_at: str
    pickup_mode: PickupMode
    return_mode: ReturnMode
    pickup_address_summary: str = Field(min_length=2, max_length=80)
    return_address_summary: str = Field(min_length=2, max_length=80)
    remark: str | None = Field(default=None, max_length=120)


class FeeEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: str
    city_code: str
    rental_days: int
    rent_fee: int
    delivery_service_fee: int
    discount_amount: int
    payable_amount: int
    vehicle_deposit_amount: int
    violation_deposit_amount: int
    price_snapshot: list[dict[str, int | str]]
    lock_minutes: int


class CustomerOrderDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    user_id: str
    vehicle_id: str
    city_code: str
    vehicle_source: str
    pickup_at: str
    return_at: str
    pickup_mode: PickupMode
    return_mode: ReturnMode
    pickup_address_summary: str
    return_address_summary: str
    remark: str | None = None
    rental_days: int
    rent_fee: int
    delivery_service_fee: int
    discount_amount: int
    payable_amount: int
    vehicle_deposit_amount: int
    violation_deposit_amount: int
    payment_status: PaymentStatus
    order_status: OrderStatus
    lock_expires_at: str
    created_at: str
    price_snapshot: list[dict[str, int | str]]
    accepted_by: str | None = None
    accepted_at: str | None = None
    original_vehicle_id: str | None = None
    reassign_price_difference: int = 0
    reassign_result: str | None = None
    return_reason: str | None = None
    operation_logs: list[dict[str, str]] = Field(default_factory=list)


class ExpireUnpaidOrdersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expired_order_ids: list[str]
    total: int


class CustomerOrderListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CustomerOrderDetail]
    total: int


class OrderAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remark: str | None = Field(default=None, max_length=120)


class OrderReturnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=2, max_length=120)


class OrderReassignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_vehicle_id: str
    remark: str | None = Field(default=None, max_length=120)


class OrderCancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default="用户取消待支付订单", max_length=120)
