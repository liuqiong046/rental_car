"""DTOs for payment prepay, callbacks, and payment flows."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentProvider = Literal["wechat_mock"]
PaymentFlowStatus = Literal["prepay_created", "paid", "failed", "cancelled"]
WechatTradeState = Literal["SUCCESS", "FAIL", "CANCEL"]


class PaymentPrepayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str


class PaymentPrepayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    order_id: str
    provider: PaymentProvider
    payable_amount: int = Field(ge=0)
    currency: Literal["CNY"] = "CNY"
    status: PaymentFlowStatus
    pay_params: dict[str, str]
    mock_callback_url: str
    created_at: str


class WechatPaymentCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    payment_id: str
    transaction_id: str = Field(min_length=4, max_length=64)
    trade_state: WechatTradeState
    paid_amount: int = Field(ge=0)


class PaymentCallbackResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    order_id: str
    transaction_id: str | None
    processed: bool
    payment_status: Literal["unpaid", "paid"]
    order_status: Literal["pending_payment", "pending_acceptance", "closed"]


class PaymentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payment_id: str
    order_id: str
    user_id: str
    provider: PaymentProvider
    payable_amount: int
    status: PaymentFlowStatus
    pay_params: dict[str, str]
    mock_callback_url: str
    created_at: str
    transaction_id: str | None = None
