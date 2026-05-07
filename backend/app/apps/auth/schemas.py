"""DTOs for customer authentication."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.apps.users.schemas import ChannelSource, CustomerProfile


class CustomerLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(pattern=r"^1\d{10}$")
    verification_code: str = Field(min_length=4, max_length=6)
    channel_source: ChannelSource | None = None


class SmsCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(pattern=r"^1\d{10}$")


class CustomerLoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: CustomerProfile
