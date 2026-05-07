"""Customer auth and profile API contract tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.anyio
async def test_customer_can_login_and_read_masked_profile() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        login_response = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": "19898766543", "verification_code": "1234"},
        )
        token = login_response.json()["access_token"]
        profile_response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert 200 == login_response.status_code
    assert 200 == profile_response.status_code
    assert "198****6543" == profile_response.json()["phone_mask"]


@pytest.mark.anyio
async def test_customer_profile_requires_login() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/users/me")

    assert 401 == response.status_code
    assert "请先登录" == response.json()["detail"]


@pytest.mark.anyio
async def test_blacklisted_customer_is_blocked_on_login() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": "19900000000", "verification_code": "1234"},
        )

    assert 403 == response.status_code
    assert "账号已被限制使用" == response.json()["detail"]


@pytest.mark.anyio
async def test_customer_login_records_channel_source() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/phone-login",
            json={
                "phone": "19898766543",
                "verification_code": "1234",
                "channel_source": {"channel_code": "douyin", "store_code": "store_01"},
            },
        )

    assert 200 == response.status_code
    assert "douyin" == response.json()["user"]["channel_source"]["channel_code"]


@pytest.mark.anyio
async def test_customer_can_request_code_update_profile_and_change_phone() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        code_response = await client.post("/api/v1/auth/sms-code", json={"phone": "19898766543"})
        login_response = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": "19898766543", "verification_code": "1234"},
        )
        token = login_response.json()["access_token"]
        profile_response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"nickname": "三亚租车客", "avatar_text": "租"},
        )
        phone_response = await client.patch(
            "/api/v1/users/me/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "19812345678", "verification_code": "1234"},
        )

    assert 204 == code_response.status_code
    assert 200 == profile_response.status_code
    assert "三亚租车客" == profile_response.json()["nickname"]
    assert "租" == profile_response.json()["avatar_text"]
    assert 200 == phone_response.status_code
    assert "198****5678" == phone_response.json()["phone_mask"]
