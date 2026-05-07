"""Vehicle availability and price calendar API contract tests."""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def _admin_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "hq_admin", "password": "hq_admin123"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_public_vehicle_list_filters_unavailable_and_missing_price() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/vehicles?city_code=SY")

    assert 200 == response.status_code
    vehicle_ids = {item["vehicle_id"] for item in response.json()["items"]}
    assert {"su7-blue", "su7-white"} == vehicle_ids
    assert "su7-maintenance" not in vehicle_ids
    assert "su7-no-price" not in vehicle_ids


@pytest.mark.anyio
async def test_missing_price_vehicle_returns_clear_unavailable_reason() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/vehicles/su7-no-price")

    assert 409 == response.status_code
    assert "当前日期缺少可租价格" == response.json()["detail"]


@pytest.mark.anyio
async def test_vehicle_source_is_explicit_for_dispatch_flow() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/vehicles?city_code=SY")

    sources = {item["vehicle_id"]: item["source"] for item in response.json()["items"]}
    assert "operation_owned" == sources["su7-blue"]
    assert "dealer" == sources["su7-white"]


@pytest.mark.anyio
async def test_public_vehicle_list_supports_customer_filters_and_time_range() -> None:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    pickup_at = f"{today.isoformat()}T10:00:00"
    return_at = f"{tomorrow.isoformat()}T10:00:00"
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get(
            "/api/v1/vehicles",
            params={
                "city_code": "SY",
                "pickup_at": pickup_at,
                "return_at": return_at,
                "brand": "小米",
                "price_min": 190,
                "price_max": 210,
                "color": "珍珠白",
                "vehicle_type": "轿车",
                "energy_type": "纯电动",
                "seats": 5,
                "gearbox": "自动挡",
            },
        )

    assert 200 == response.status_code
    payload = response.json()
    assert 1 == payload["total"]
    assert "su7-white" == payload["items"][0]["vehicle_id"]
    assert "plate_no" not in payload["items"][0]
    assert "琼 B •••• 18" == payload["items"][0]["plate_mask"]


@pytest.mark.anyio
async def test_public_vehicle_detail_returns_price_calendar_without_full_plate() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/vehicles/su7-blue")

    assert 200 == response.status_code
    payload = response.json()
    assert "plate_no" not in payload
    assert "琼 B •••• 29" == payload["plate_mask"]
    assert len(payload["price_calendar"]) >= 7
    assert all("base_price" not in day for day in payload["price_calendar"])
    assert {"date", "customer_price", "rentable", "available_periods"} <= set(
        payload["price_calendar"][0].keys()
    )


@pytest.mark.anyio
async def test_admin_can_update_price_and_make_vehicle_available() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _admin_token(client)
        price_response = await client.put(
            "/api/v1/vehicles/admin/items/su7-no-price/prices",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "date": __import__("datetime").date.today().isoformat(),
                "base_price": 180,
                "customer_price": 218,
                "wholesale_price": 160,
                "rentable": True,
                "available_periods": ["00:00-24:00"],
            },
        )
        public_response = await client.get("/api/v1/vehicles?city_code=SY")

    assert 200 == price_response.status_code
    vehicle_ids = {item["vehicle_id"] for item in public_response.json()["items"]}
    assert "su7-no-price" in vehicle_ids


@pytest.mark.anyio
async def test_admin_can_create_model_vehicle_and_batch_prices() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _admin_token(client)
        model_response = await client.post(
            "/api/v1/vehicles/admin/models",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "brand": "奔驰",
                "series": "E级",
                "model_name": "奔驰 E300L",
                "year": 2024,
                "vehicle_type": "轿车",
                "energy_type": "汽油",
                "seats": 5,
                "gearbox": "自动挡",
                "min_base_price": 300,
                "deposit_amount": 10000,
                "violation_deposit_amount": 3000,
            },
        )
        model_id = model_response.json()["model_id"]
        vehicle_response = await client.post(
            "/api/v1/vehicles/admin/items",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "city_code": "SY",
                "model_id": model_id,
                "plate_mask": "琼 B •••• 36",
                "color": "曜石黑",
                "mileage_km": 8000,
                "daily_mileage_limit": 300,
                "image_url": "/assets/car-black.jpg",
                "source": "dealer",
                "dealer_id": "org_dealer_a",
                "review_status": "approved",
                "listing_status": "listed",
            },
        )
        vehicle_id = vehicle_response.json()["vehicle_id"]
        start_date = date.today().isoformat()
        batch_response = await client.put(
            f"/api/v1/vehicles/admin/items/{vehicle_id}/prices/batch",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "start_date": start_date,
                "days": 90,
                "base_price": 320,
                "customer_price": 388,
                "wholesale_price": 300,
                "rentable": True,
                "available_periods": ["00:00-24:00"],
            },
        )
        public_response = await client.get(
            "/api/v1/vehicles",
            params={"city_code": "SY", "brand": "奔驰", "price_min": 380, "price_max": 400},
        )

    assert 201 == model_response.status_code
    assert 201 == vehicle_response.status_code
    assert "dealer" == vehicle_response.json()["source"]
    assert 90 == batch_response.json()["total"]
    assert 1 == public_response.json()["total"]
    assert vehicle_id == public_response.json()["items"][0]["vehicle_id"]


@pytest.mark.anyio
async def test_admin_price_conflict_and_vehicle_delete_constraints() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _admin_token(client)
        conflict_response = await client.put(
            "/api/v1/vehicles/admin/items/su7-blue/prices",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "date": date.today().isoformat(),
                "base_price": 170,
                "customer_price": 160,
                "wholesale_price": 150,
                "rentable": True,
                "available_periods": ["00:00-24:00"],
            },
        )
        locked_response = await client.delete(
            "/api/v1/vehicles/admin/items/su7-blue",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert 400 == conflict_response.status_code
    assert "C端价不能低于底价" == conflict_response.json()["detail"]
    assert 409 == locked_response.status_code
    assert "仍有价格或订单占用" == locked_response.json()["detail"]


@pytest.mark.anyio
async def test_time_range_availability_excludes_overlapping_unpaid_lock() -> None:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        first_response = await client.get(
            "/api/v1/vehicles",
            params={
                "city_code": "SY",
                "pickup_at": f"{today.isoformat()}T10:00:00",
                "return_at": f"{today.isoformat()}T20:00:00",
            },
        )
        token_response = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": "19898766543", "verification_code": "1234"},
        )
        token = token_response.json()["access_token"]
        await client.post(
            "/api/v1/identity/submissions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "real_name": "张三",
                "id_no": "460200199001010011",
                "driver_license_no": "DRIVER12345",
                "id_card_front_url": "mock://front",
                "id_card_back_url": "mock://back",
                "driver_license_url": "mock://driver",
            },
        )
        admin_token = await _admin_token(client)
        submissions = await client.get(
            "/api/v1/identity/admin/submissions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        await client.post(
            f"/api/v1/identity/admin/submissions/{submissions.json()['items'][0]['submission_id']}/review",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "approved"},
        )
        create_order_response = await client.post(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "lock-overlap"},
            json={
                "vehicle_id": "su7-blue",
                "city_code": "SY",
                "pickup_at": f"{today.isoformat()}T10:00:00",
                "return_at": f"{today.isoformat()}T20:00:00",
                "pickup_mode": "self_pickup",
                "return_mode": "self_return",
                "pickup_address_summary": "三亚运营中心",
                "return_address_summary": "三亚运营中心",
            },
        )
        overlap_response = await client.get(
            "/api/v1/vehicles",
            params={
                "city_code": "SY",
                "pickup_at": f"{today.isoformat()}T12:00:00",
                "return_at": f"{today.isoformat()}T18:00:00",
            },
        )
        next_day_response = await client.get(
            "/api/v1/vehicles",
            params={
                "city_code": "SY",
                "pickup_at": f"{tomorrow.isoformat()}T10:00:00",
                "return_at": f"{tomorrow.isoformat()}T20:00:00",
            },
        )

    assert 200 == first_response.status_code
    assert 201 == create_order_response.status_code
    overlap_ids = {item["vehicle_id"] for item in overlap_response.json()["items"]}
    next_day_ids = {item["vehicle_id"] for item in next_day_response.json()["items"]}
    assert "su7-blue" not in overlap_ids
    assert "su7-blue" in next_day_ids
