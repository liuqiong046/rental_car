"""In-memory vehicle catalog and availability service."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status

from app.apps.admin.schemas import AdminActor
from app.apps.vehicles.schemas import (
    PriceCalendarBatchUpdateRequest,
    PriceCalendarEntry,
    PriceCalendarUpdateRequest,
    VehicleCreateRequest,
    VehicleDetail,
    VehicleListResponse,
    VehicleModel,
    VehicleModelCreateRequest,
    VehicleModelListResponse,
    VehicleModelUpdateRequest,
    VehiclePublicSearch,
    VehicleStatusUpdateRequest,
    VehicleUpdateRequest,
)


class VehicleInventoryService:
    def __init__(self) -> None:
        # TODO(WF-P0-06/WF-P0-08/WF-P0-09): 当前为内存车型/车辆/价格种子；
        # 后续需补车型库、车辆 CRUD、批量价格、取还时间库存和订单占用计算。
        self.models = _seed_models()
        self.vehicles = _seed_vehicles(self.models)
        self.prices = _seed_prices()
        self.occupancies: dict[str, list[dict[str, str]]] = {}

    def list_public_available(self, filters: VehiclePublicSearch) -> VehicleListResponse:
        rental_range = _optional_rental_range(filters.pickup_at, filters.return_at)
        rental_dates = rental_range.dates if rental_range else [_today()]
        items = []
        for vehicle in self.vehicles.values():
            if filters.city_code and vehicle.city_code != filters.city_code.upper():
                continue
            enriched = self._with_availability(vehicle, rental_dates, rental_range)
            if not _matches_public_filters(enriched, filters):
                continue
            if enriched.available:
                items.append(enriched)
        return VehicleListResponse(items=items, total=len(items))

    def get_public_vehicle(self, vehicle_id: str) -> VehicleDetail:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
        enriched = self._with_availability(vehicle)
        if not enriched.available:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=enriched.unavailable_reason)
        return enriched

    def get_vehicle_for_order_state(self, vehicle_id: str) -> VehicleDetail:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
        return self._with_availability(vehicle)

    def get_available_for_order(
        self,
        vehicle_id: str,
        pickup_at: str,
        return_at: str,
    ) -> VehicleDetail:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
        rental_range = _rental_range(pickup_at, return_at)
        enriched = self._with_availability(vehicle, rental_range.dates, rental_range)
        if not enriched.available:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=enriched.unavailable_reason)
        return enriched

    def calculate_customer_rent_fee(
        self,
        vehicle_id: str,
        pickup_at: str,
        return_at: str,
    ) -> tuple[int, int]:
        dates = _rental_dates(pickup_at, return_at)
        prices = [self.prices[_price_key(vehicle_id, day)].customer_price for day in dates]
        return len(dates), sum(prices)

    def calculate_wholesale_rent_fee(
        self,
        vehicle_id: str,
        pickup_at: str,
        return_at: str,
    ) -> tuple[int, int]:
        dates = _rental_dates(pickup_at, return_at)
        prices = [self.prices[_price_key(vehicle_id, day)].wholesale_price for day in dates]
        return len(dates), sum(prices)

    def lock_for_unpaid_order(
        self,
        vehicle_id: str,
        pickup_at: str | None = None,
        return_at: str | None = None,
        order_id: str | None = None,
    ) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
        if pickup_at and return_at:
            rental_range = _rental_range(pickup_at, return_at)
            locks = [
                lock
                for lock in self.occupancies.get(vehicle_id, [])
                if not (order_id and lock.get("order_id") == order_id)
            ]
            locks.append(
                {
                    "order_id": order_id or f"manual:{_now_iso()}",
                    "pickup_at": rental_range.pickup_at.isoformat(),
                    "return_at": rental_range.return_at.isoformat(),
                }
            )
            self.occupancies[vehicle_id] = locks
        self.vehicles[vehicle_id] = vehicle.model_copy(update={"occupied": True})

    def release_unpaid_order_lock(self, vehicle_id: str, order_id: str | None = None) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            return
        if order_id is None:
            self.occupancies.pop(vehicle_id, None)
        else:
            remaining = [
                lock for lock in self.occupancies.get(vehicle_id, []) if lock.get("order_id") != order_id
            ]
            if remaining:
                self.occupancies[vehicle_id] = remaining
            else:
                self.occupancies.pop(vehicle_id, None)
        occupied = bool(self.occupancies.get(vehicle_id))
        self.vehicles[vehicle_id] = vehicle.model_copy(update={"occupied": occupied})

    def list_models(self, actor: AdminActor) -> VehicleModelListResponse:
        _ = actor
        items = list(self.models.values())
        return VehicleModelListResponse(items=items, total=len(items))

    def create_model(self, actor: AdminActor, payload: VehicleModelCreateRequest) -> VehicleModel:
        _ = actor
        model_id = _next_model_id(payload.brand, payload.series, self.models)
        model = VehicleModel(model_id=model_id, **payload.model_dump())
        self.models[model_id] = model
        return model

    def update_model(
        self,
        actor: AdminActor,
        model_id: str,
        payload: VehicleModelUpdateRequest,
    ) -> VehicleModel:
        _ = actor
        model = self._get_model(model_id)
        updated = model.model_copy(update=payload.model_dump(exclude_none=True))
        self.models[model_id] = updated
        for vehicle_id, vehicle in self.vehicles.items():
            if vehicle.model.model_id == model_id:
                self.vehicles[vehicle_id] = vehicle.model_copy(update={"model": updated})
        return updated

    def delete_model(self, actor: AdminActor, model_id: str) -> None:
        _ = actor
        self._get_model(model_id)
        if any(vehicle.model.model_id == model_id for vehicle in self.vehicles.values()):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="车型仍有关联车辆")
        del self.models[model_id]

    def list_admin_vehicles(self, actor: AdminActor) -> VehicleListResponse:
        items = [
            self._with_availability(vehicle)
            for vehicle in self.vehicles.values()
            if _is_city_visible(actor, vehicle.city_code)
        ]
        return VehicleListResponse(items=items, total=len(items))

    def create_vehicle(self, actor: AdminActor, payload: VehicleCreateRequest) -> VehicleDetail:
        if not _is_city_visible(actor, payload.city_code.upper()):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        model = self._get_model(payload.model_id)
        vehicle_id = _next_vehicle_id(model, payload.color, self.vehicles)
        vehicle = VehicleDetail(
            vehicle_id=vehicle_id,
            city_code=payload.city_code.upper(),
            model=model,
            plate_mask=payload.plate_mask,
            color=payload.color,
            mileage_km=payload.mileage_km,
            daily_mileage_limit=payload.daily_mileage_limit,
            image_url=payload.image_url,
            source=payload.source,
            dealer_id=payload.dealer_id,
            hosted_owner=payload.hosted_owner,
            review_status=payload.review_status,
            listing_status=payload.listing_status,
            maintenance=False,
            manually_locked=False,
            occupied=False,
            available=False,
        )
        self.vehicles[vehicle_id] = vehicle
        return self._with_availability(vehicle)

    def update_vehicle(
        self,
        actor: AdminActor,
        vehicle_id: str,
        payload: VehicleUpdateRequest,
    ) -> VehicleDetail:
        vehicle = self._get_admin_vehicle(actor, vehicle_id)
        changes = payload.model_dump(exclude_none=True)
        if "city_code" in changes:
            changes["city_code"] = changes["city_code"].upper()
            if not _is_city_visible(actor, changes["city_code"]):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        if "model_id" in changes:
            changes["model"] = self._get_model(changes.pop("model_id"))
        updated = vehicle.model_copy(update=changes)
        self.vehicles[vehicle_id] = updated
        return self._with_availability(updated)

    def delete_vehicle(self, actor: AdminActor, vehicle_id: str) -> None:
        self._get_admin_vehicle(actor, vehicle_id)
        has_prices = any(key.startswith(f"{vehicle_id}:") for key in self.prices)
        has_occupancy = bool(self.occupancies.get(vehicle_id))
        if has_prices or has_occupancy:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="仍有价格或订单占用")
        del self.vehicles[vehicle_id]

    def update_vehicle_status(
        self,
        actor: AdminActor,
        vehicle_id: str,
        payload: VehicleStatusUpdateRequest,
    ) -> VehicleDetail:
        vehicle = self._get_admin_vehicle(actor, vehicle_id)
        updated = vehicle.model_copy(
            update={
                key: value
                for key, value in {
                    "review_status": payload.review_status,
                    "listing_status": payload.listing_status,
                    "maintenance": payload.maintenance,
                    "manually_locked": payload.manually_locked,
                }.items()
                if value is not None
            },
        )
        self.vehicles[vehicle_id] = updated
        return self._with_availability(updated)

    def list_price_calendar(
        self,
        actor: AdminActor,
        vehicle_id: str,
    ) -> dict[str, object]:
        self._get_admin_vehicle(actor, vehicle_id)
        items = [entry for key, entry in self.prices.items() if key.startswith(f"{vehicle_id}:")]
        return {"items": items, "total": len(items)}

    def upsert_price(
        self,
        actor: AdminActor,
        vehicle_id: str,
        payload: PriceCalendarUpdateRequest,
    ) -> PriceCalendarEntry:
        vehicle = self._get_admin_vehicle(actor, vehicle_id)
        self._validate_price(vehicle, payload.base_price, payload.customer_price, payload.wholesale_price)
        entry = PriceCalendarEntry(
            vehicle_id=vehicle_id,
            date=payload.date,
            base_price=payload.base_price,
            customer_price=payload.customer_price,
            wholesale_price=payload.wholesale_price,
            rentable=payload.rentable,
            available_periods=payload.available_periods,
            updated_at=_now_iso(),
        )
        self.prices[_price_key(vehicle_id, payload.date)] = entry
        return entry

    def upsert_prices_batch(
        self,
        actor: AdminActor,
        vehicle_id: str,
        payload: PriceCalendarBatchUpdateRequest,
    ) -> dict[str, object]:
        vehicle = self._get_admin_vehicle(actor, vehicle_id)
        self._validate_price(vehicle, payload.base_price, payload.customer_price, payload.wholesale_price)
        try:
            start_date = date.fromisoformat(payload.start_date)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="价格日期格式不正确") from exc
        items = []
        for offset in range(payload.days):
            day = (start_date + timedelta(days=offset)).isoformat()
            entry = PriceCalendarEntry(
                vehicle_id=vehicle_id,
                date=day,
                base_price=payload.base_price,
                customer_price=payload.customer_price,
                wholesale_price=payload.wholesale_price,
                rentable=payload.rentable,
                available_periods=payload.available_periods,
                updated_at=_now_iso(),
            )
            self.prices[_price_key(vehicle_id, day)] = entry
            items.append(entry)
        return {"items": items, "total": len(items)}

    def _get_admin_vehicle(self, actor: AdminActor, vehicle_id: str) -> VehicleDetail:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
        if not _is_city_visible(actor, vehicle.city_code):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        return vehicle

    def _get_model(self, model_id: str) -> VehicleModel:
        model = self.models.get(model_id)
        if model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车型不存在")
        return model

    def _validate_price(
        self,
        vehicle: VehicleDetail,
        base_price: int,
        customer_price: int,
        wholesale_price: int,
    ) -> None:
        if base_price < vehicle.model.min_base_price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="底价低于车型最低价")
        if customer_price < base_price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="C端价不能低于底价")
        if wholesale_price > customer_price:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="批发价不能高于C端价")

    def _with_availability(
        self,
        vehicle: VehicleDetail,
        rental_dates: list[str] | None = None,
        rental_range: "RentalRange | None" = None,
    ) -> VehicleDetail:
        dates = rental_dates or [_today()]
        price = self.prices.get(_price_key(vehicle.vehicle_id, dates[0]))
        price_calendar = self._public_calendar(vehicle.vehicle_id)
        unavailable_reason = _unavailable_reason(
            vehicle,
            self.prices,
            dates,
            self.occupancies.get(vehicle.vehicle_id, []),
            rental_range,
        )
        occupied = bool(self.occupancies.get(vehicle.vehicle_id))
        return vehicle.model_copy(
            update={
                "available": unavailable_reason is None,
                "unavailable_reason": unavailable_reason,
                "today_price": price,
                "price_calendar": price_calendar,
                "occupied": occupied,
            },
        )

    def _public_calendar(self, vehicle_id: str) -> list[PriceCalendarEntry]:
        days = [_today_date() + timedelta(days=offset) for offset in range(14)]
        return [
            self.prices[key]
            for day in days
            if (key := _price_key(vehicle_id, day.isoformat())) in self.prices
        ]


def _seed_models() -> dict[str, VehicleModel]:
    model = VehicleModel(
        model_id="model_su7_2024",
        brand="小米",
        series="SU7",
        model_name="小米汽车 SU7",
        year=2024,
        vehicle_type="轿车",
        energy_type="纯电动",
        seats=5,
        gearbox="自动挡",
        min_base_price=160,
        deposit_amount=8000,
        violation_deposit_amount=3000,
    )
    return {model.model_id: model}


def _seed_vehicles(models: dict[str, VehicleModel]) -> dict[str, VehicleDetail]:
    base = {
        "city_code": "SY",
        "model": models["model_su7_2024"],
        "color": "海湾蓝",
        "mileage_km": 12000,
        "daily_mileage_limit": 300,
        "image_url": "/assets/car-blue.jpg",
        "review_status": "approved",
        "listing_status": "listed",
        "maintenance": False,
        "manually_locked": False,
        "occupied": False,
        "available": False,
    }
    vehicles = [
        VehicleDetail(
            **base,
            vehicle_id="su7-blue",
            plate_mask="琼 B •••• 29",
            source="operation_owned",
        ),
        VehicleDetail(
            **{**base, "image_url": "/assets/car-white.jpg", "color": "珍珠白"},
            vehicle_id="su7-white",
            plate_mask="琼 B •••• 18",
            source="dealer",
            dealer_id="org_dealer_a",
        ),
        VehicleDetail(
            **{**base, "maintenance": True},
            vehicle_id="su7-maintenance",
            plate_mask="琼 B •••• 88",
            source="hosted",
            hosted_owner="托管车主A",
        ),
        VehicleDetail(
            **base,
            vehicle_id="su7-no-price",
            plate_mask="琼 B •••• 66",
            source="operation_owned",
        ),
    ]
    return {vehicle.vehicle_id: vehicle for vehicle in vehicles}


def _seed_prices() -> dict[str, PriceCalendarEntry]:
    prices: dict[str, PriceCalendarEntry] = {}
    for offset in range(14):
        day = (_today_date() + timedelta(days=offset)).isoformat()
        prices[_price_key("su7-blue", day)] = _price("su7-blue", day, 180, 197 + offset % 3, 150)
        prices[_price_key("su7-white", day)] = _price("su7-white", day, 180, 207 + offset % 3, 155)
        prices[_price_key("su7-maintenance", day)] = _price(
            "su7-maintenance",
            day,
            180,
            207,
            155,
        )
    return prices


def _price(vehicle_id: str, day: str, base_price: int, customer_price: int, wholesale_price: int):
    return PriceCalendarEntry(
        vehicle_id=vehicle_id,
        date=day,
        base_price=base_price,
        customer_price=customer_price,
        wholesale_price=wholesale_price,
        rentable=True,
        available_periods=["00:00-24:00"],
        updated_at=_now_iso(),
    )


@dataclass(frozen=True)
class RentalRange:
    pickup_at: datetime
    return_at: datetime
    dates: list[str]


def _unavailable_reason(
    vehicle: VehicleDetail,
    prices: dict[str, PriceCalendarEntry],
    rental_dates: list[str],
    occupancies: list[dict[str, str]],
    rental_range: RentalRange | None,
) -> str | None:
    if vehicle.review_status != "approved":
        return "车辆未审核通过"
    if vehicle.listing_status != "listed":
        return "车辆已下架"
    if vehicle.maintenance:
        return "车辆维保中"
    if vehicle.manually_locked:
        return "车辆已锁定"
    if vehicle.occupied and not occupancies:
        return "车辆已被占用"
    if rental_range and _has_overlapping_occupancy(occupancies, rental_range):
        return "车辆已被占用"
    if any(
        (price := prices.get(_price_key(vehicle.vehicle_id, day))) is None or not price.rentable
        for day in rental_dates
    ):
        return "当前日期缺少可租价格"
    return None


def _matches_public_filters(vehicle: VehicleDetail, filters: VehiclePublicSearch) -> bool:
    price = vehicle.today_price.customer_price if vehicle.today_price else None
    checks = [
        filters.brand is None
        or any(
            _text_matches(filters.brand, value)
            for value in (vehicle.model.brand, vehicle.model.series, vehicle.model.model_name)
        ),
        filters.color is None or filters.color == vehicle.color,
        filters.vehicle_type is None or filters.vehicle_type == vehicle.model.vehicle_type,
        filters.energy_type is None or filters.energy_type == vehicle.model.energy_type,
        filters.seats is None or filters.seats == vehicle.model.seats,
        filters.gearbox is None or filters.gearbox == vehicle.model.gearbox,
        filters.price_min is None or (price is not None and price >= filters.price_min),
        filters.price_max is None or (price is not None and price <= filters.price_max),
    ]
    return all(checks)


def _text_matches(expected: str, actual: str) -> bool:
    return expected in actual or actual in expected


def _rental_dates(pickup_at: str | None, return_at: str | None) -> list[str]:
    if not pickup_at or not return_at:
        return [_today()]
    return _rental_range(pickup_at, return_at).dates


def _optional_rental_range(pickup_at: str | None, return_at: str | None) -> RentalRange | None:
    if not pickup_at and not return_at:
        return None
    if not pickup_at or not return_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="取还车时间不能为空")
    return _rental_range(pickup_at, return_at)


def _rental_range(pickup_at: str, return_at: str) -> RentalRange:
    try:
        pickup = datetime.fromisoformat(pickup_at)
        return_time = datetime.fromisoformat(return_at)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="取还车时间格式不正确") from exc
    if return_time <= pickup:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="还车时间不能早于取车时间")
    pickup_date = pickup.date()
    return_date = return_time.date()
    if return_date < pickup_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="还车时间不能早于取车时间")
    days = (return_date - pickup_date).days + 1
    dates = [(pickup_date + timedelta(days=offset)).isoformat() for offset in range(days)]
    return RentalRange(pickup_at=pickup, return_at=return_time, dates=dates)


def _has_overlapping_occupancy(occupancies: list[dict[str, str]], rental_range: RentalRange) -> bool:
    for lock in occupancies:
        try:
            locked_pickup = datetime.fromisoformat(lock["pickup_at"])
            locked_return = datetime.fromisoformat(lock["return_at"])
        except (KeyError, ValueError):
            return True
        if rental_range.pickup_at < locked_return and locked_pickup < rental_range.return_at:
            return True
    return False


def _is_city_visible(actor: AdminActor, city_code: str) -> bool:
    scope = actor.role.data_scope
    return scope.type == "all" or scope.city_code == city_code


def _price_key(vehicle_id: str, day: str) -> str:
    return f"{vehicle_id}:{day}"


def _next_model_id(
    brand: str,
    series: str,
    models: dict[str, VehicleModel],
) -> str:
    prefix = f"model_{_slug(brand)}_{_slug(series)}"
    return _next_id(prefix, set(models))


def _next_vehicle_id(
    model: VehicleModel,
    color: str,
    vehicles: dict[str, VehicleDetail],
) -> str:
    prefix = f"{_slug(model.brand)}-{_slug(model.series)}-{_slug(color)}"
    return _next_id(prefix, set(vehicles))


def _next_id(prefix: str, existing_ids: set[str]) -> str:
    candidate = prefix
    index = 2
    while candidate in existing_ids:
        candidate = f"{prefix}-{index}"
        index += 1
    return candidate


def _slug(value: str) -> str:
    normalized = "".join(char.lower() for char in value if char.isalnum())
    return normalized or "item"


def _today() -> str:
    return _today_date().isoformat()


def _today_date() -> date:
    return date.today()


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


vehicle_inventory_service = VehicleInventoryService()
