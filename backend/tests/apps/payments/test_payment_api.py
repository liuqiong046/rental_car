"""Payment prepay and callback API contract tests."""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.apps.vehicles.service import vehicle_inventory_service
from app.main import create_app


async def _customer_token(client: AsyncClient, phone: str) -> str:
    response = await client.post(
        "/api/v1/auth/phone-login",
        json={"phone": phone, "verification_code": "1234"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


async def _approved_customer_token(client: AsyncClient, phone: str) -> str:
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
    reviewed = await client.post(
        f"/api/v1/identity/admin/submissions/{submitted.json()['submission_id']}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "approved"},
    )
    assert 200 == reviewed.status_code
    return token


async def _admin_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "hq_admin", "password": "hq_admin123"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


def _order_payload(vehicle_id: str) -> dict[str, object]:
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
        "remark": "支付测试",
    }


def _vehicle_query_from_order(order_payload: dict[str, object]) -> dict[str, object]:
    return {
        "city_code": order_payload["city_code"],
        "pickup_at": order_payload["pickup_at"],
        "return_at": order_payload["return_at"],
    }


async def _pending_order(client: AsyncClient, token: str, vehicle_id: str) -> dict[str, object]:
    response = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": f"order-{vehicle_id}"},
        json=_order_payload(vehicle_id),
    )
    assert 201 == response.status_code
    return response.json()


def _release_payment_test_locks() -> None:
    vehicle_inventory_service.release_unpaid_order_lock("su7-blue")
    vehicle_inventory_service.release_unpaid_order_lock("su7-white")


@pytest.mark.anyio
async def test_customer_can_create_wechat_mock_prepay_for_own_pending_order() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            token = await _approved_customer_token(client, "19898766101")
            order = await _pending_order(client, token, "su7-blue")
            headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "prepay-blue"}
            first = await client.post(
                "/api/v1/payments/prepay",
                headers=headers,
                json={"order_id": order["order_id"]},
            )
            second = await client.post(
                "/api/v1/payments/prepay",
                headers=headers,
                json={"order_id": order["order_id"]},
            )
    finally:
        _release_payment_test_locks()
    assert 201 == first.status_code
    assert 201 == second.status_code
    first_payload = first.json()
    second_payload = second.json()
    assert order["order_id"] == first_payload["order_id"]
    assert "wechat_mock" == first_payload["provider"]
    assert order["payable_amount"] == first_payload["payable_amount"]
    assert first_payload["payment_id"] == second_payload["payment_id"]
    assert first_payload["mock_callback_url"].endswith("/api/v1/payments/wechat/callback")
    assert first_payload["pay_params"]["package"].startswith("prepay_id=")


@pytest.mark.anyio
async def test_wechat_success_callback_advances_order_once() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            token = await _approved_customer_token(client, "19898766102")
            order = await _pending_order(client, token, "su7-white")
            prepay = await client.post(
                "/api/v1/payments/prepay",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "prepay-white"},
                json={"order_id": order["order_id"]},
            )
            callback_payload = {
                "order_id": order["order_id"],
                "payment_id": prepay.json()["payment_id"],
                "transaction_id": "wx-tx-0001",
                "trade_state": "SUCCESS",
                "paid_amount": order["payable_amount"],
            }
            first = await client.post(
                "/api/v1/payments/wechat/callback",
                headers={"Idempotency-Key": "callback-white-first"},
                json=callback_payload,
            )
            repeated = await client.post(
                "/api/v1/payments/wechat/callback",
                headers={"Idempotency-Key": "callback-white-repeat"},
                json=callback_payload,
            )
    finally:
        _release_payment_test_locks()
    assert 200 == first.status_code
    assert 200 == repeated.status_code
    assert True is first.json()["processed"]
    assert False is repeated.json()["processed"]
    assert "paid" == first.json()["payment_status"]
    assert "pending_acceptance" == first.json()["order_status"]
    assert "paid" == repeated.json()["payment_status"]
    assert "pending_acceptance" == repeated.json()["order_status"]


@pytest.mark.anyio
async def test_customer_cannot_prepay_other_users_order() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            owner_token = await _approved_customer_token(client, "19898766103")
            other_token = await _approved_customer_token(client, "19898766104")
            order = await _pending_order(client, owner_token, "su7-blue")
            response = await client.post(
                "/api/v1/payments/prepay",
                headers={
                    "Authorization": f"Bearer {other_token}",
                    "Idempotency-Key": "prepay-forbidden",
                },
                json={"order_id": order["order_id"]},
            )
    finally:
        _release_payment_test_locks()
    assert 403 == response.status_code
    assert "只能支付本人订单" == response.json()["detail"]


@pytest.mark.anyio
async def test_success_callback_rejects_amount_mismatch() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            token = await _approved_customer_token(client, "19898766105")
            order = await _pending_order(client, token, "su7-white")
            prepay = await client.post(
                "/api/v1/payments/prepay",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "prepay-mismatch"},
                json={"order_id": order["order_id"]},
            )
            response = await client.post(
                "/api/v1/payments/wechat/callback",
                headers={"Idempotency-Key": "callback-mismatch"},
                json={
                    "order_id": order["order_id"],
                    "payment_id": prepay.json()["payment_id"],
                    "transaction_id": "wx-tx-mismatch",
                    "trade_state": "SUCCESS",
                    "paid_amount": order["payable_amount"] - 1,
                },
            )
    finally:
        _release_payment_test_locks()
    assert 400 == response.status_code
    assert "支付金额不一致" == response.json()["detail"]


@pytest.mark.anyio
async def test_paid_order_is_not_expired_by_unpaid_cleanup() -> None:
    order_payload = _order_payload("su7-blue")
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            token = await _approved_customer_token(client, "19898766106")
            admin_token = await _admin_token(client)
            order = await _pending_order(client, token, "su7-blue")
            prepay = await client.post(
                "/api/v1/payments/prepay",
                headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "prepay-no-expire"},
                json={"order_id": order["order_id"]},
            )
            paid = await client.post(
                "/api/v1/payments/wechat/callback",
                headers={"Idempotency-Key": "callback-no-expire"},
                json={
                    "order_id": order["order_id"],
                    "payment_id": prepay.json()["payment_id"],
                    "transaction_id": "wx-tx-no-expire",
                    "trade_state": "SUCCESS",
                    "paid_amount": order["payable_amount"],
                },
            )
            expired = await client.post(
                "/api/v1/orders/admin/expire-unpaid?minutes_after_lock=1",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            vehicles = await client.get("/api/v1/vehicles", params=_vehicle_query_from_order(order_payload))

    finally:
        _release_payment_test_locks()
    assert 200 == paid.status_code
    assert 200 == expired.status_code
    assert order["order_id"] not in expired.json()["expired_order_ids"]
    vehicle_ids = {item["vehicle_id"] for item in vehicles.json()["items"]}
    assert "su7-blue" not in vehicle_ids
