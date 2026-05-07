"""City configuration and rule API contract tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def _admin_token(client: AsyncClient, username: str = "hq_admin") -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": username, "password": f"{username}123"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_public_city_list_only_returns_active_cities() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/cities")

    assert 200 == response.status_code
    codes = {item["city_code"] for item in response.json()["items"]}
    assert "SY" in codes
    assert "HN" not in codes


@pytest.mark.anyio
async def test_disabled_city_cannot_be_read_by_customer_side() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/cities/HN")

    assert 404 == response.status_code
    assert "城市未开通" == response.json()["detail"]


@pytest.mark.anyio
async def test_admin_rule_update_increments_version_and_public_reads_latest() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _admin_token(client)
        before = await client.get("/api/v1/cities/SY")
        before_version = before.json()["config_version"]
        update = await client.patch(
            "/api/v1/cities/admin/configs/SY",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "rules": {
                    "unpaid_lock_minutes": 20,
                    "dealer_confirm_sla_minutes": 45,
                    "service_radius_km": 25,
                    "over_radius_fee_per_km": 10,
                    "night_service_fee": 80,
                    "holiday_source": "platform_calendar",
                    "early_return_refund_rule": "提前还车按人工审核退费",
                    "cancellation_refund_rule": "支付前免费取消，支付后按规则退费",
                }
            },
        )
        latest = await client.get("/api/v1/cities/SY")

    assert 200 == update.status_code
    assert before_version + 1 == update.json()["config_version"]
    assert 20 == latest.json()["rules"]["unpaid_lock_minutes"]


@pytest.mark.anyio
async def test_city_admin_cannot_update_other_city() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _admin_token(client, "ops_admin")
        response = await client.patch(
            "/api/v1/cities/admin/configs/HN",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "active"},
        )

    assert 403 == response.status_code
    assert "无权限" == response.json()["detail"]


@pytest.mark.anyio
async def test_admin_can_create_city_with_store_and_deposit_rules() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _admin_token(client)
        create_response = await client.post(
            "/api/v1/cities/admin/configs",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "city_code": "XM",
                "city_name": "厦门",
                "status": "active",
                "default_operation_center_id": "org_sanya",
                "service_categories": ["租车", "送车上门"],
                "contact_name": "厦门运营",
                "contact_phone_mask": "198****0001",
                "store_address": "思明区环岛路门店",
                "business_hours": "09:00-21:00",
                "map_fence": {
                    "center_latitude": 24.48,
                    "center_longitude": 118.08,
                    "radius_km": 30,
                },
                "homepage": {
                    "banner_titles": ["厦门安心租车"],
                    "hot_brands": ["奔驰E", "小米SU7"],
                    "recommended_vehicle_ids": [],
                },
                "rules": {
                    "unpaid_lock_minutes": 15,
                    "dealer_confirm_sla_minutes": 30,
                    "service_radius_km": 30,
                    "over_radius_fee_per_km": 9,
                    "night_service_fee": 80,
                    "deposit_amount": 5000,
                    "violation_deposit_amount": 3000,
                    "holiday_source": "platform_calendar",
                    "early_return_refund_rule": "提前还车按人工审核退费",
                    "cancellation_refund_rule": "支付前免费取消，支付后按规则退费",
                },
            },
        )
        public_response = await client.get("/api/v1/cities/XM")

    assert 201 == create_response.status_code
    assert "思明区环岛路门店" == create_response.json()["store_address"]
    assert 5000 == create_response.json()["rules"]["deposit_amount"]
    assert 200 == public_response.status_code
    assert "XM" == public_response.json()["city_code"]
