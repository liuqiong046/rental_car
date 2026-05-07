"""Order confirmation, fee estimate, and unpaid lock API contract tests."""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.apps.orders.service import customer_order_service
from app.apps.payments.service import payment_service
from app.apps.vehicles.service import vehicle_inventory_service
from app.main import create_app


async def _customer_token(client: AsyncClient, phone: str = "19898766543") -> str:
    response = await client.post(
        "/api/v1/auth/phone-login",
        json={"phone": phone, "verification_code": "1234"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


async def _approved_customer_token(client: AsyncClient, phone: str = "19898766543") -> str:
    token = await _customer_token(client, phone)
    submitted = await client.post(
        "/api/v1/identity/submissions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "real_name": "张三",
            "id_no": "460200199001011234",
            "driver_license_no": "460200199001019999",
            "id_card_front_url": "mock://front",
            "id_card_back_url": "mock://back",
            "driver_license_url": "mock://license",
        },
    )
    admin_token = await _admin_token(client)
    await client.post(
        f"/api/v1/identity/admin/submissions/{submitted.json()['submission_id']}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "approved"},
    )
    return token


async def _admin_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "hq_admin", "password": "hq_admin123"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


def _order_payload(vehicle_id: str = "su7-blue") -> dict[str, object]:
    pickup = date.today()
    return_day = pickup + timedelta(days=1)
    return {
        "vehicle_id": vehicle_id,
        "city_code": "SY",
        "pickup_at": f"{pickup.isoformat()}T10:00:00",
        "return_at": f"{return_day.isoformat()}T10:00:00",
        "pickup_mode": "self_pickup",
        "return_mode": "self_return",
        "pickup_address_summary": "三亚运营中心",
        "return_address_summary": "三亚运营中心",
        "remark": "需要满电",
    }


def _vehicle_query_from_order(order_payload: dict[str, object]) -> dict[str, object]:
    return {
        "city_code": order_payload["city_code"],
        "pickup_at": order_payload["pickup_at"],
        "return_at": order_payload["return_at"],
    }


def _reset_order_test_state() -> None:
    vehicle_inventory_service.release_unpaid_order_lock("su7-blue")
    vehicle_inventory_service.release_unpaid_order_lock("su7-white")
    customer_order_service.orders.clear()
    customer_order_service.idempotency_index.clear()
    customer_order_service.operation_idempotency_index.clear()
    payment_service.payments.clear()
    payment_service.prepay_idempotency_index.clear()
    payment_service.callback_idempotency_index.clear()
    payment_service.order_payment_index.clear()
    payment_service.success_transaction_index.clear()


@pytest.fixture(autouse=True)
def reset_order_state() -> None:
    _reset_order_test_state()
    yield
    _reset_order_test_state()


@pytest.mark.anyio
async def test_estimate_returns_fee_snapshot_and_deposit_policy() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _customer_token(client)
        response = await client.post(
            "/api/v1/orders/estimate",
            headers={"Authorization": f"Bearer {token}"},
            json=_order_payload(),
        )

    assert 200 == response.status_code
    payload = response.json()
    assert 2 == payload["rental_days"]
    assert 395 == payload["rent_fee"]
    assert 0 == payload["delivery_service_fee"]
    assert 395 == payload["payable_amount"]
    assert 8000 == payload["vehicle_deposit_amount"]
    assert 3000 == payload["violation_deposit_amount"]


@pytest.mark.anyio
async def test_unapproved_customer_cannot_create_pending_payment_order() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _customer_token(client, "19898766545")
        response = await client.post(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-unapproved"},
            json=_order_payload(),
        )

    assert 403 == response.status_code
    assert "身份认证通过后才能提交订单" == response.json()["detail"]


@pytest.mark.anyio
async def test_create_order_locks_vehicle_until_unpaid_expiration() -> None:
    payload = _order_payload()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _approved_customer_token(client)
        create_response = await client.post(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-lock"},
            json=payload,
        )
        list_response = await client.get("/api/v1/vehicles", params=_vehicle_query_from_order(payload))
        admin_token = await _admin_token(client)
        cleanup = await client.post(
            "/api/v1/orders/admin/expire-unpaid?minutes_after_lock=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert 201 == create_response.status_code
    order = create_response.json()
    assert "pending_payment" == order["order_status"]
    assert "unpaid" == order["payment_status"]
    assert order["lock_expires_at"]
    vehicle_ids = {item["vehicle_id"] for item in list_response.json()["items"]}
    assert "su7-blue" not in vehicle_ids
    assert 200 == cleanup.status_code


@pytest.mark.anyio
async def test_repeated_idempotency_key_returns_original_order() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _approved_customer_token(client)
        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "idem-repeat"}
        first = await client.post("/api/v1/orders", headers=headers, json=_order_payload("su7-white"))
        second = await client.post("/api/v1/orders", headers=headers, json=_order_payload("su7-white"))
        admin_token = await _admin_token(client)
        cleanup = await client.post(
            "/api/v1/orders/admin/expire-unpaid?minutes_after_lock=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert 201 == first.status_code
    assert 201 == second.status_code
    assert first.json()["order_id"] == second.json()["order_id"]
    assert 200 == cleanup.status_code


@pytest.mark.anyio
async def test_admin_expire_unpaid_orders_releases_vehicle() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        customer_token = await _approved_customer_token(client)
        admin_token = await _admin_token(client)
        created = await client.post(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": "idem-expire"},
            json=_order_payload(),
        )
        expired = await client.post(
            "/api/v1/orders/admin/expire-unpaid?minutes_after_lock=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        available = await client.get("/api/v1/vehicles?city_code=SY")

    assert 201 == created.status_code
    assert 200 == expired.status_code
    assert [created.json()["order_id"]] == expired.json()["expired_order_ids"]
    vehicle_ids = {item["vehicle_id"] for item in available.json()["items"]}
    assert "su7-blue" in vehicle_ids


@pytest.mark.anyio
async def test_customer_can_cancel_own_pending_payment_order_and_release_vehicle() -> None:
    payload = _order_payload()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        customer_token = await _approved_customer_token(client, "19898766566")
        created = await client.post(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {customer_token}", "Idempotency-Key": "idem-cancel"},
            json=payload,
        )
        cancelled = await client.post(
            f"/api/v1/orders/{created.json()['order_id']}/cancel",
            headers={"Authorization": f"Bearer {customer_token}"},
        )
        available = await client.get("/api/v1/vehicles", params=_vehicle_query_from_order(payload))

    assert 201 == created.status_code
    assert 200 == cancelled.status_code
    assert "closed" == cancelled.json()["order_status"]
    assert "unpaid" == cancelled.json()["payment_status"]
    vehicle_ids = {item["vehicle_id"] for item in available.json()["items"]}
    assert "su7-blue" in vehicle_ids
