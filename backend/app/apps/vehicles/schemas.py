"""DTOs for vehicles, price calendar, and availability."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VehicleSource = Literal["operation_owned", "hosted", "dealer"]
ReviewStatus = Literal["pending", "approved", "rejected"]
ListingStatus = Literal["listed", "unlisted"]


class VehicleModel(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    model_id: str
    brand: str
    series: str
    model_name: str
    year: int
    vehicle_type: str
    energy_type: str
    seats: int
    gearbox: str
    min_base_price: int
    deposit_amount: int
    violation_deposit_amount: int


class VehicleModelCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    brand: str = Field(min_length=1, max_length=24)
    series: str = Field(min_length=1, max_length=24)
    model_name: str = Field(min_length=2, max_length=48)
    year: int = Field(ge=2000, le=2100)
    vehicle_type: str = Field(min_length=1, max_length=24)
    energy_type: str = Field(min_length=1, max_length=24)
    seats: int = Field(ge=1, le=20)
    gearbox: str = Field(min_length=1, max_length=24)
    min_base_price: int = Field(ge=0)
    deposit_amount: int = Field(ge=0)
    violation_deposit_amount: int = Field(ge=0)


class VehicleModelUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    brand: str | None = Field(default=None, min_length=1, max_length=24)
    series: str | None = Field(default=None, min_length=1, max_length=24)
    model_name: str | None = Field(default=None, min_length=2, max_length=48)
    year: int | None = Field(default=None, ge=2000, le=2100)
    vehicle_type: str | None = Field(default=None, min_length=1, max_length=24)
    energy_type: str | None = Field(default=None, min_length=1, max_length=24)
    seats: int | None = Field(default=None, ge=1, le=20)
    gearbox: str | None = Field(default=None, min_length=1, max_length=24)
    min_base_price: int | None = Field(default=None, ge=0)
    deposit_amount: int | None = Field(default=None, ge=0)
    violation_deposit_amount: int | None = Field(default=None, ge=0)


class VehicleModelListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VehicleModel]
    total: int


class PriceCalendarEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: str
    date: str
    base_price: int = Field(ge=0)
    customer_price: int = Field(ge=0)
    wholesale_price: int = Field(ge=0)
    rentable: bool
    available_periods: list[str]
    updated_at: str


class PublicPriceCalendarEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: str
    date: str
    customer_price: int = Field(ge=0)
    rentable: bool
    available_periods: list[str]


class VehicleDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehicle_id: str
    city_code: str
    model: VehicleModel
    plate_mask: str
    color: str
    mileage_km: int
    daily_mileage_limit: int
    image_url: str
    source: VehicleSource
    dealer_id: str | None = None
    hosted_owner: str | None = None
    review_status: ReviewStatus
    listing_status: ListingStatus
    maintenance: bool
    manually_locked: bool
    occupied: bool
    available: bool
    unavailable_reason: str | None = None
    today_price: PriceCalendarEntry | None = None
    price_calendar: list[PriceCalendarEntry] = Field(default_factory=list)


class VehicleListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VehicleDetail]
    total: int


class VehicleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    city_code: str = Field(min_length=2, max_length=12)
    model_id: str
    plate_mask: str = Field(min_length=4, max_length=24)
    color: str = Field(min_length=1, max_length=24)
    mileage_km: int = Field(ge=0)
    daily_mileage_limit: int = Field(ge=0)
    image_url: str = Field(min_length=1, max_length=160)
    source: VehicleSource
    dealer_id: str | None = Field(default=None, max_length=32)
    hosted_owner: str | None = Field(default=None, max_length=32)
    review_status: ReviewStatus = "pending"
    listing_status: ListingStatus = "unlisted"


class VehicleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    city_code: str | None = Field(default=None, min_length=2, max_length=12)
    model_id: str | None = None
    plate_mask: str | None = Field(default=None, min_length=4, max_length=24)
    color: str | None = Field(default=None, min_length=1, max_length=24)
    mileage_km: int | None = Field(default=None, ge=0)
    daily_mileage_limit: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, min_length=1, max_length=160)
    source: VehicleSource | None = None
    dealer_id: str | None = Field(default=None, max_length=32)
    hosted_owner: str | None = Field(default=None, max_length=32)


class PublicVehicleDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    vehicle_id: str
    city_code: str
    model: VehicleModel
    plate_mask: str
    color: str
    mileage_km: int
    daily_mileage_limit: int
    image_url: str
    source: VehicleSource
    available: bool
    unavailable_reason: str | None = None
    today_price: PublicPriceCalendarEntry | None = None
    price_calendar: list[PublicPriceCalendarEntry] = Field(default_factory=list)


class PublicVehicleListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PublicVehicleDetail]
    total: int


class VehiclePublicSearch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city_code: str | None = None
    pickup_at: str | None = None
    return_at: str | None = None
    brand: str | None = None
    price_min: int | None = Field(default=None, ge=0)
    price_max: int | None = Field(default=None, ge=0)
    color: str | None = None
    vehicle_type: str | None = None
    energy_type: str | None = None
    seats: int | None = Field(default=None, ge=1)
    gearbox: str | None = None


class PriceCalendarListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PriceCalendarEntry]
    total: int


class VehicleStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: ReviewStatus | None = None
    listing_status: ListingStatus | None = None
    maintenance: bool | None = None
    manually_locked: bool | None = None


class PriceCalendarUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    base_price: int = Field(ge=0)
    customer_price: int = Field(ge=0)
    wholesale_price: int = Field(ge=0)
    rentable: bool = True
    available_periods: list[str] = Field(default_factory=lambda: ["00:00-24:00"])


class PriceCalendarBatchUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: str
    days: int = Field(ge=1, le=90)
    base_price: int = Field(ge=0)
    customer_price: int = Field(ge=0)
    wholesale_price: int = Field(ge=0)
    rentable: bool = True
    available_periods: list[str] = Field(default_factory=lambda: ["00:00-24:00"])
