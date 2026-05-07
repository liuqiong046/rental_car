"""Identity verification API contract tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def _customer_token(client: AsyncClient) -> str:
    return await _customer_token_for_phone(client, "19898766543")


async def _customer_token_for_phone(client: AsyncClient, phone: str) -> str:
    response = await client.post(
        "/api/v1/auth/phone-login",
        json={"phone": phone, "verification_code": "1234"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


async def _admin_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "hq_admin", "password": "hq_admin123"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_customer_submit_identity_returns_masked_fields() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _customer_token(client)
        response = await client.post(
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

    assert 201 == response.status_code
    payload = response.json()
    assert "pending" == payload["status"]
    assert "4602********1234" == payload["id_no_mask"]
    assert "id_no" not in payload


@pytest.mark.anyio
async def test_admin_reject_reason_syncs_to_customer_side() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        customer_token = await _customer_token(client)
        admin_token = await _admin_token(client)
        submitted = await client.post(
            "/api/v1/identity/submissions",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "real_name": "李四",
                "id_no": "460200199101011234",
                "driver_license_no": "460200199101019999",
                "id_card_front_url": "mock://front",
                "id_card_back_url": "mock://back",
                "driver_license_url": "mock://license",
            },
        )
        submission_id = submitted.json()["submission_id"]
        await client.post(
            f"/api/v1/identity/admin/submissions/{submission_id}/review",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "rejected", "reject_reason": "证件照片不清晰"},
        )
        result = await client.get(
            "/api/v1/identity/me",
            headers={"Authorization": f"Bearer {customer_token}"},
        )

    assert 200 == result.status_code
    assert "rejected" == result.json()["status"]
    assert "证件照片不清晰" == result.json()["reject_reason"]


@pytest.mark.anyio
async def test_rejected_or_missing_identity_can_be_checked_before_payment() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _customer_token_for_phone(client, "19898766544")
        response = await client.get("/api/v1/identity/me", headers={"Authorization": f"Bearer {token}"})

    assert 404 == response.status_code
    assert "尚未提交身份认证" == response.json()["detail"]


@pytest.mark.anyio
async def test_customer_can_prepare_identity_asset_and_resubmit_after_rejection() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        customer_token = await _customer_token_for_phone(client, "19898766545")
        upload_token = await client.post(
            "/api/v1/identity/assets",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={"file_name": "id-front.jpg", "content_type": "image/jpeg"},
        )
        first = await client.post(
            "/api/v1/identity/submissions",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "real_name": "王五",
                "id_no": "460200199201011234",
                "driver_license_no": "460200199201019999",
                "id_card_front_url": upload_token.json()["asset_url"],
                "id_card_back_url": "mock://back",
                "driver_license_url": "mock://license",
            },
        )
        admin_token = await _admin_token(client)
        await client.post(
            f"/api/v1/identity/admin/submissions/{first.json()['submission_id']}/review",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "rejected", "reject_reason": "驾驶证照片缺角"},
        )
        second = await client.post(
            "/api/v1/identity/submissions",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "real_name": "王五",
                "id_no": "460200199201011234",
                "driver_license_no": "460200199201019999",
                "id_card_front_url": "mock://front-v2",
                "id_card_back_url": "mock://back-v2",
                "driver_license_url": "mock://license-v2",
            },
        )

    assert 201 == upload_token.status_code
    assert upload_token.json()["asset_url"].startswith("mock://identity-assets/")
    assert 1 == first.json()["version"]
    assert 2 == second.json()["version"]
    assert "pending" == second.json()["status"]
    assert second.json()["submission_id"] != first.json()["submission_id"]


@pytest.mark.anyio
async def test_admin_detail_can_authorize_credential_preview_and_records_audit_log() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        customer_token = await _customer_token_for_phone(client, "19898766546")
        submitted = await client.post(
            "/api/v1/identity/submissions",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "real_name": "赵六",
                "id_no": "460200199301011234",
                "driver_license_no": "460200199301019999",
                "id_card_front_url": "mock://front",
                "id_card_back_url": "mock://back",
                "driver_license_url": "mock://license",
            },
        )
        admin_token = await _admin_token(client)
        detail = await client.get(
            f"/api/v1/identity/admin/submissions/{submitted.json()['submission_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        preview = await client.post(
            f"/api/v1/identity/admin/submissions/{submitted.json()['submission_id']}/authorize-preview",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "人工审核证件照片"},
        )
        detail_after_preview = await client.get(
            f"/api/v1/identity/admin/submissions/{submitted.json()['submission_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert 200 == detail.status_code
    assert detail.json()["customer"]["phone_mask"].startswith("198")
    assert "id_no" not in detail.json()
    assert [] == detail.json()["audit_logs"]
    assert 200 == preview.status_code
    assert preview.json()["id_card_front_url"].startswith("mock://identity/authorized-preview")
    assert "id_no" not in preview.json()
    logs = detail_after_preview.json()["audit_logs"]
    assert [{"action": "authorize_preview", "actor_id": "acct_hq", "reason": "人工审核证件照片"}] == [
        {key: log[key] for key in ("action", "actor_id", "reason")} for log in logs
    ]
