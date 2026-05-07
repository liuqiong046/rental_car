"""DTOs for city configuration and operational rules."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CityStatus = Literal["active", "disabled"]


class HomepageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    banner_titles: list[str] = Field(min_length=1, max_length=5)
    hot_brands: list[str] = Field(min_length=1, max_length=10)
    recommended_vehicle_ids: list[str] = Field(default_factory=list, max_length=20)


class ServiceRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unpaid_lock_minutes: int = Field(ge=5, le=120)
    dealer_confirm_sla_minutes: int = Field(ge=10, le=1440)
    service_radius_km: int = Field(ge=1, le=100)
    over_radius_fee_per_km: int = Field(ge=0, le=200)
    night_service_fee: int = Field(ge=0, le=1000)
    deposit_amount: int = Field(default=5000, ge=0, le=200000)
    violation_deposit_amount: int = Field(default=3000, ge=0, le=200000)
    holiday_source: str = Field(min_length=2, max_length=32)
    early_return_refund_rule: str = Field(min_length=2, max_length=80)
    cancellation_refund_rule: str = Field(min_length=2, max_length=80)


class MapFenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    center_latitude: float = Field(ge=-90, le=90)
    center_longitude: float = Field(ge=-180, le=180)
    radius_km: int = Field(ge=1, le=200)


class CityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city_code: str
    city_name: str
    status: CityStatus
    default_operation_center_id: str
    service_categories: list[str]
    contact_name: str
    contact_phone_mask: str
    store_address: str
    business_hours: str
    map_fence: MapFenceConfig
    homepage: HomepageConfig
    rules: ServiceRuleConfig
    is_default: bool
    config_version: int
    updated_at: str


class CityConfigListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CityConfig]
    total: int


class CityConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CityStatus | None = None
    default_operation_center_id: str | None = None
    contact_name: str | None = Field(default=None, min_length=2, max_length=32)
    contact_phone_mask: str | None = Field(default=None, min_length=8, max_length=16)
    store_address: str | None = Field(default=None, min_length=2, max_length=80)
    business_hours: str | None = Field(default=None, min_length=5, max_length=32)
    map_fence: MapFenceConfig | None = None
    homepage: HomepageConfig | None = None
    rules: ServiceRuleConfig | None = None
    service_categories: list[str] | None = None


class CityConfigCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city_code: str = Field(min_length=2, max_length=12)
    city_name: str = Field(min_length=2, max_length=24)
    status: CityStatus
    default_operation_center_id: str
    service_categories: list[str] = Field(min_length=1, max_length=10)
    contact_name: str = Field(min_length=2, max_length=32)
    contact_phone_mask: str = Field(min_length=8, max_length=16)
    store_address: str = Field(min_length=2, max_length=80)
    business_hours: str = Field(min_length=5, max_length=32)
    map_fence: MapFenceConfig
    homepage: HomepageConfig
    rules: ServiceRuleConfig
