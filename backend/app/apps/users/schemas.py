"""DTOs for customer user profiles."""

from pydantic import BaseModel, ConfigDict, Field


class ChannelSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_code: str | None = Field(default=None, max_length=32)
    store_code: str | None = Field(default=None, max_length=32)
    promoter_code: str | None = Field(default=None, max_length=32)


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    nickname: str
    avatar_text: str
    phone_mask: str
    certification_status: str
    channel_source: ChannelSource | None = None
    blacklisted: bool = False


class CustomerProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nickname: str | None = Field(default=None, min_length=1, max_length=24)
    avatar_text: str | None = Field(default=None, min_length=1, max_length=2)


class CustomerPhoneUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(pattern=r"^1\d{10}$")
    verification_code: str = Field(min_length=4, max_length=6)
