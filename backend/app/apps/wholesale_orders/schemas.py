"""DTOs for wholesale order confirmation loop."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WholesaleOrderStatus = Literal["pending_dealer_acceptance", "accepted", "rejected", "expired_rejected"]


class WholesaleOrderDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wholesale_order_id: str
    customer_order_id: str | None = None
    city_code: str
    vehicle_id: str
    dealer_id: str
    pickup_at: str
    return_at: str
    rental_days: int
    wholesale_price: int
    status: WholesaleOrderStatus
    reject_reason: str | None = None
    created_by: str
    created_at: str
    expires_at: str
    accepted_by: str | None = None
    accepted_at: str | None = None
    operation_logs: list[dict[str, str]] = Field(default_factory=list)


class WholesaleOrderListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WholesaleOrderDetail]
    total: int


class WholesaleOrderCreateRelatedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_order_id: str
    remark: str | None = Field(default=None, max_length=120)


class WholesaleOrderAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remark: str | None = Field(default=None, max_length=120)


class WholesaleOrderRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=2, max_length=120)


class WholesaleOrderChangePriceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wholesale_price: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=120)


class ExpireWholesaleOrdersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expired_wholesale_order_ids: list[str]
    total: int
