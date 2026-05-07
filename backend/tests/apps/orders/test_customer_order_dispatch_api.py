"""Customer order dispatch state machine API contract tests."""

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.apps.orders.service import customer_order_service
from app.apps.payments.service import payment_service
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


async def _admin_token(client: AsyncClient, username: str = "hq_admin") -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": username, "password": f"{username}123"},
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
        "remark": "接单测试",
    }


async def _paid_order(client: AsyncClient, phone: str, vehicle_id: str) -> dict[str, object]:
    token = await _approved_customer_token(client, phone)
    order = await client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": f"order-{phone}"},
        json=_order_payload(vehicle_id),
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


def _release_dispatch_test_locks() -> None:
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


@pytest.mark.anyio
async def test_paid_order_appears_in_admin_pending_acceptance_list() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_order(client, "19898766201", "su7-blue")
            admin_token = await _admin_token(client, "ops_admin")
            response = await client.get(
                "/api/v1/orders/admin/customer-orders?status=pending_acceptance",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            detail = await client.get(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
    finally:
        _release_dispatch_test_locks()
    assert 200 == response.status_code
    payload = response.json()
    assert 1 <= payload["total"]
    assert paid["order_id"] in {item["order_id"] for item in payload["items"]}
    assert 200 == detail.status_code
    assert "pending_acceptance" == detail.json()["order_status"]


@pytest.mark.anyio
async def test_accept_operation_owned_order_enters_pending_dispatch_idempotently() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_order(client, "19898766202", "su7-blue")
            admin_token = await _admin_token(client, "ops_admin")
            headers = {"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "accept-blue"}
            first = await client.post(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}/accept",
                headers=headers,
                json={"remark": "自有车辆确认接单"},
            )
            repeated = await client.post(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}/accept",
                headers=headers,
                json={"remark": "重复提交"},
            )
    finally:
        _release_dispatch_test_locks()
    assert 200 == first.status_code
    assert 200 == repeated.status_code
    assert "pending_dispatch" == first.json()["order_status"]
    assert first.json()["order_id"] == repeated.json()["order_id"]
    assert 1 == len([log for log in repeated.json()["operation_logs"] if log["action"] == "accept"])


@pytest.mark.anyio
async def test_dealer_vehicle_cannot_be_accepted_without_wholesale_order() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_order(client, "19898766203", "su7-white")
            admin_token = await _admin_token(client, "ops_admin")
            response = await client.post(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}/accept",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "accept-dealer"},
                json={"remark": "车行车辆接单"},
            )
    finally:
        _release_dispatch_test_locks()
    assert 409 == response.status_code
    assert "车行车辆需创建关联批发订单" == response.json()["detail"]


@pytest.mark.anyio
async def test_reassign_same_model_vehicle_records_price_difference() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_order(client, "19898766204", "su7-blue")
            admin_token = await _admin_token(client, "ops_admin")
            response = await client.post(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}/reassign",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "reassign-white"},
                json={"target_vehicle_id": "su7-white", "remark": "自有车无法履约，改派同车型"},
            )
    finally:
        _release_dispatch_test_locks()
    assert 200 == response.status_code
    payload = response.json()
    assert "pending_dispatch" == payload["order_status"]
    assert "su7-blue" == payload["original_vehicle_id"]
    assert "su7-white" == payload["vehicle_id"]
    assert 0 < payload["reassign_price_difference"]
    assert "运营中心承担差价" == payload["reassign_result"]


@pytest.mark.anyio
async def test_return_order_moves_to_pending_return() -> None:
    try:
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            paid = await _paid_order(client, "19898766205", "su7-blue")
            admin_token = await _admin_token(client, "ops_admin")
            response = await client.post(
                f"/api/v1/orders/admin/customer-orders/{paid['order_id']}/return",
                headers={"Authorization": f"Bearer {admin_token}", "Idempotency-Key": "return-blue"},
                json={"reason": "车辆临时不可用"},
            )
    finally:
        _release_dispatch_test_locks()
    assert 200 == response.status_code
    assert "pending_return" == response.json()["order_status"]
    assert "车辆临时不可用" == response.json()["return_reason"]
