"""In-memory city configuration service with versioned rules."""

from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.apps.admin.schemas import AdminActor
from app.apps.cities.schemas import (
    CityConfig,
    CityConfigCreateRequest,
    CityConfigUpdateRequest,
    HomepageConfig,
    MapFenceConfig,
    ServiceRuleConfig,
)


class CityConfigService:
    def __init__(self) -> None:
        # TODO(WF-P0-05): 当前为城市规则最小内存配置；后续需补城市/运营中心 CRUD、
        # 门店地址、地图围栏、服务费规则版本发布和首页运营完整配置。
        self.cities = _seed_cities()

    def list_public_cities(self) -> dict[str, object]:
        items = [city for city in self.cities.values() if city.status == "active"]
        return {"items": items, "total": len(items)}

    def get_public_city(self, city_code: str) -> CityConfig:
        city = self.cities.get(city_code.upper())
        if city is None or city.status != "active":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="城市未开通")
        return city

    def list_admin_cities(self, actor: AdminActor) -> dict[str, object]:
        items = [city for city in self.cities.values() if _is_city_visible(actor, city)]
        return {"items": items, "total": len(items)}

    def create_city(self, actor: AdminActor, payload: CityConfigCreateRequest) -> CityConfig:
        if actor.role.data_scope.type != "all":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")
        code = payload.city_code.upper()
        if code in self.cities:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="城市已存在")

        city = CityConfig(
            city_code=code,
            city_name=payload.city_name,
            status=payload.status,
            default_operation_center_id=payload.default_operation_center_id,
            service_categories=payload.service_categories,
            contact_name=payload.contact_name,
            contact_phone_mask=payload.contact_phone_mask,
            store_address=payload.store_address,
            business_hours=payload.business_hours,
            map_fence=payload.map_fence,
            homepage=payload.homepage,
            rules=payload.rules,
            is_default=False,
            config_version=1,
            updated_at=_now_iso(),
        )
        self.cities[code] = city
        return city

    def update_city(
        self,
        actor: AdminActor,
        city_code: str,
        payload: CityConfigUpdateRequest,
    ) -> CityConfig:
        code = city_code.upper()
        city = self.cities.get(code)
        if city is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="城市不存在")
        if not _is_city_visible(actor, city):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限")

        updated = city.model_copy(
            update={
                key: value
                for key, value in {
                    "status": payload.status,
                    "default_operation_center_id": payload.default_operation_center_id,
                    "contact_name": payload.contact_name,
                    "contact_phone_mask": payload.contact_phone_mask,
                    "store_address": payload.store_address,
                    "business_hours": payload.business_hours,
                    "map_fence": payload.map_fence,
                    "homepage": payload.homepage,
                    "rules": payload.rules,
                    "service_categories": payload.service_categories,
                    "config_version": city.config_version + 1,
                    "updated_at": _now_iso(),
                }.items()
                if value is not None
            },
        )
        self.cities[code] = updated
        return updated


def _seed_cities() -> dict[str, CityConfig]:
    sanya = CityConfig(
        city_code="SY",
        city_name="三亚",
        status="active",
        default_operation_center_id="org_sanya",
        service_categories=["租车"],
        contact_name="三亚运营",
        contact_phone_mask="198****6543",
        store_address="三亚市海棠湾山海门店",
        business_hours="09:00-21:00",
        map_fence=MapFenceConfig(center_latitude=18.25, center_longitude=109.51, radius_km=20),
        homepage=HomepageConfig(
            banner_titles=["高端租车安心出行"],
            hot_brands=["小米SU7", "奔驰E", "保时捷"],
            recommended_vehicle_ids=["su7-blue", "su7-white"],
        ),
        rules=ServiceRuleConfig(
            unpaid_lock_minutes=15,
            dealer_confirm_sla_minutes=30,
            service_radius_km=20,
            over_radius_fee_per_km=8,
            night_service_fee=60,
            deposit_amount=5000,
            violation_deposit_amount=3000,
            holiday_source="platform_calendar",
            early_return_refund_rule="按城市规则人工审核退费",
            cancellation_refund_rule="未支付自动关闭，已支付按责任方退费",
        ),
        is_default=True,
        config_version=1,
        updated_at=_now_iso(),
    )
    disabled = sanya.model_copy(
        update={
            "city_code": "HN",
            "city_name": "海口",
            "status": "disabled",
            "is_default": False,
            "config_version": 1,
        },
    )
    return {city.city_code: city for city in [sanya, disabled]}


def _is_city_visible(actor: AdminActor, city: CityConfig) -> bool:
    scope = actor.role.data_scope
    if scope.type == "all":
        return True
    if scope.type == "city":
        return city.city_code == scope.city_code
    return city.default_operation_center_id == actor.organization.parent_id


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


city_config_service = CityConfigService()
