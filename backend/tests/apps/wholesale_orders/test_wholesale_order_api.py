"""Wholesale order loop API contract tests."""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.apps.orders.service import customer_order_service
from app.apps.payments.service import payment_service
from app.apps.vehicles.service import vehicle_inventory_service
from app.apps.wholesale_orders.service import wholesale_order_service
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


async def _admin_token(client: AsyncClient, username: str = "ops_admin") -> str:
    password = "dealer_active123" if username == "dealer_active" else f"{username}123"
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": username, "password": password},
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
        "remark": "批发订单测试",
    }


async def _paid_dealer_order(client: AsyncClient, phone: str = "19898766301") -> dict[str, object]:
    token = await _approved_customer_token(client, phone)
    order = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": f"order-{phone}"},
        json=_order_payload("su7-white"),
    )
    assert 201 == order.status_code
    prepay = await client.post(
        "/api/v1/payments/prepay",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": f"prepay-{phone}"},
        json={"order_id": order.json()["order_id"]},
    )
    assert 201 == prepay.status_code
    paid = await client.post(
        "/api/v1/payments/wechat/callback",
        headers={"Idempotency-Key": f"callback-{phone}"},
        json={
            "order_id": order.json()["order_id"],
            "payment_id": prepay.json()["payment_id"],
            "transaction_id": f"wx-tx-{phone}",
            "trade_state": "SUCCESS",
            "paid_amount": order.json()["payable_amount"],
        },
    )
    assert 200 == paid.status_code
    return paid.json()


def _release_wholesale_test_state() -> None:
    vehicle_inventory_service.release_unpaid_order_lock("su7-white")
    customer_order_service.orders.clear()
    customer_order_service.idempotency_index.clear()
    customer_order_service.operation_idempotency_index.clear()
    payment_service.payments.clear()
    payment_service.prepay_idempotency_index.clear()
    payment_service.callback_idempotency_index.clear()
    payment_service.order_payment_index.clear()
    payment_service.success_transaction_index.clear()
    wholesale_order_service.orders.clear()
    wholesale_order_service.related_customer_index.clear()
    wholesale_order_service.idempotency_index.clear()


@pytest.mark.anyio
async def test_create_related_wholesale_order_for_dealer_customer_order_idempotently() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_dealer_order(client)
            admin_token = await _admin_token(client, "ops_admin")
            headers = {"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "create-wholesale"}
            first = await client.post(
                "/api/v1/wholesale-orders/admin/related",
                headers=headers,
                json={"customer_order_id": paid["order_id"], "remark": "车行车辆发起批发确认"},
            )
            repeated = await client.post(
                "/api/v1/wholesale-orders/admin/related",
                headers=headers,
                json={"customer_order_id": paid["order_id"], "remark": "重复提交"},
            )
    finally:
        _release_wholesale_test_state()
    assert 201 == first.status_code
    assert 201 == repeated.status_code
    assert first.json()["wholesale_order_id"] == repeated.json()["wholesale_order_id"]
    assert paid["order_id"] == first.json()["customer_order_id"]
    assert "pending_dealer_acceptance" == first.json()["status"]
    assert "org_dealer_a" == first.json()["dealer_id"]
    assert 0 < first.json()["wholesale_price"]


@pytest.mark.anyio
async def test_dealer_accepts_related_wholesale_order_and_customer_order_enters_dispatch() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_dealer_order(client, "19898766302")
            admin_token = await _admin_token(client, "ops_admin")
            created = await client.post(
                "/api/v1/wholesale-orders/admin/related",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "create-accept"},
                json={"customer_order_id": paid["order_id"]},
            )
            dealer_token = await _admin_token(client, "dealer_active")
            first = await client.post(
                f"/api/v1/wholesale-orders/{created.json()['wholesale_order_id']}/accept",
                headers={"Authorization": f"Bearer {dealer_token}", "Idempotency-Key": "accept-wholesale"},
                json={"remark": "车行确认接单"},
            )
            repeated = await client.post(
                f"/api/v1/wholesale-orders/{created.json()['wholesale_order_id']}/accept",
                headers={"Authorization": f"Bearer {dealer_token}", "Idempotency-Key": "accept-wholesale"},
                json={"remark": "重复接单"},
            )
            detail = await client.get(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
    finally:
        _release_wholesale_test_state()
    assert 200 == first.status_code
    assert 200 == repeated.status_code
    assert "accepted" == first.json()["status"]
    assert "pending_dispatch" == detail.json()["order_status"]
    assert 1 == len([log for log in first.json()["operation_logs"] if log["action"] == "accept"])


@pytest.mark.anyio
async def test_dealer_can_change_wholesale_price_before_accepting() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_dealer_order(client, "19898766303")
            admin_token = await _admin_token(client, "ops_admin")
            created = await client.post(
                "/api/v1/wholesale-orders/admin/related",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "create-price"},
                json={"customer_order_id": paid["order_id"]},
            )
            dealer_token = await _admin_token(client, "dealer_active")
            response = await client.post(
                f"/api/v1/wholesale-orders/{created.json()['wholesale_order_id']}/change-price",
                headers={"Authorization": f"Bearer {dealer_token}", "Idempotency-Key": "change-price"},
                json={"wholesale_price": 199, "reason": "节假日车源紧张"},
            )
    finally:
        _release_wholesale_test_state()
    assert 200 == response.status_code
    assert 199 == response.json()["wholesale_price"]
    assert "pending_dealer_acceptance" == response.json()["status"]
    assert "change_price" == response.json()["operation_logs"][-1]["action"]


@pytest.mark.anyio
async def test_reject_related_wholesale_order_moves_customer_order_to_reassign() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_dealer_order(client, "19898766304")
            admin_token = await _admin_token(client, "ops_admin")
            created = await client.post(
                "/api/v1/wholesale-orders/admin/related",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "create-reject"},
                json={"customer_order_id": paid["order_id"]},
            )
            dealer_token = await _admin_token(client, "dealer_active")
            response = await client.post(
                f"/api/v1/wholesale-orders/{created.json()['wholesale_order_id']}/reject",
                headers={"Authorization": f"Bearer {dealer_token}", "Idempotency-Key": "reject-wholesale"},
                json={"reason": "车辆已被线下占用"},
            )
            detail = await client.get(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
    finally:
        _release_wholesale_test_state()
    assert 200 == response.status_code
    assert "rejected" == response.json()["status"]
    assert "pending_reassign" == detail.json()["order_status"]
    assert "批发订单已拒绝：车辆已被线下占用" == detail.json()["return_reason"]


@pytest.mark.anyio
async def test_expire_pending_wholesale_orders_rejects_by_city_sla() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_dealer_order(client, "19898766305")
            admin_token = await _admin_token(client, "ops_admin")
            created = await client.post(
                "/api/v1/wholesale-orders/admin/related",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "create-expire"},
                json={"customer_order_id": paid["order_id"]},
            )
            response = await client.post(
                "/api/v1/wholesale-orders/admin/expire-pending?minutes_after_sla=1",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            detail = await client.get(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
    finally:
        _release_wholesale_test_state()
    assert 200 == response.status_code
    assert [created.json()["wholesale_order_id"]] == response.json()["expired_wholesale_order_ids"]
    assert 1 == response.json()["total"]
    assert "pending_reassign" == detail.json()["order_status"]
