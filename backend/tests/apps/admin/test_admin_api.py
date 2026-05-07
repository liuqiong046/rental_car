"""Admin auth and RBAC API contract tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def _login(client: AsyncClient, username: str) -> str:
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": username, "password": f"{username}123"},
    )
    assert 200 == response.status_code
    return response.json()["access_token"]


@pytest.mark.anyio
async def test_admin_login_and_me_returns_actor_scope() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _login(client, "hq_admin")
        response = await client.get("/api/v1/admin/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert 200 == response.status_code
    payload = response.json()
    assert "hq_admin" == payload["username"]
    assert "all" == payload["role"]["data_scope"]["type"]


@pytest.mark.anyio
async def test_inactive_admin_account_cannot_login() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/admin/auth/login",
            json={"username": "disabled_admin", "password": "disabled_admin123"},
        )

    assert 403 == response.status_code
    assert "账号不可用" == response.json()["detail"]


@pytest.mark.anyio
async def test_admin_routes_require_login() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/v1/admin/accounts")

    assert 401 == response.status_code
    assert "请先登录" == response.json()["detail"]


@pytest.mark.anyio
async def test_city_admin_only_sees_city_scoped_accounts() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _login(client, "ops_admin")
        response = await client.get(
            "/api/v1/admin/accounts",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert 200 == response.status_code
    usernames = {item["username"] for item in response.json()["items"]}
    assert "hq_admin" not in usernames
    assert {"ops_admin", "disabled_admin"} <= usernames


@pytest.mark.anyio
async def test_admin_can_create_and_disable_scoped_account() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _login(client, "hq_admin")
        create_response = await client.post(
            "/api/v1/admin/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "finance_admin",
                "display_name": "财务管理员",
                "password": "finance_admin123",
                "organization_id": "org_sanya",
                "role_id": "role_ops_admin",
            },
        )
        account_id = create_response.json()["account_id"]
        disable_response = await client.patch(
            f"/api/v1/admin/accounts/{account_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"},
        )

    assert 201 == create_response.status_code
    assert 200 == disable_response.status_code
    assert "disabled" == disable_response.json()["status"]


@pytest.mark.anyio
async def test_admin_can_manage_organization_role_and_account_details() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _login(client, "hq_admin")
        org_response = await client.post(
            "/api/v1/admin/organizations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "亚龙湾车行",
                "type": "dealer",
                "parent_id": "org_sanya",
                "city_code": "SY",
            },
        )
        org_id = org_response.json()["id"]
        role_response = await client.post(
            "/api/v1/admin/roles",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "support",
                "name": "客服主管",
                "menus": ["dashboard", "accounts"],
                "buttons": ["account:create"],
                "data_scope": {"type": "organization", "organization_id": org_id},
            },
        )
        role_id = role_response.json()["id"]
        account_response = await client.post(
            "/api/v1/admin/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "support_admin",
                "display_name": "客服管理员",
                "password": "support_admin123",
                "organization_id": org_id,
                "role_id": role_id,
            },
        )
        account_id = account_response.json()["account_id"]
        edit_response = await client.patch(
            f"/api/v1/admin/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "display_name": "客服值班主管",
                "organization_id": org_id,
                "role_id": role_id,
            },
        )
        lock_response = await client.patch(
            f"/api/v1/admin/accounts/{account_id}/status",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "locked"},
        )
        reset_response = await client.post(
            f"/api/v1/admin/accounts/{account_id}/reset-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"password": "support_admin_new123"},
        )
        org_disable_response = await client.patch(
            f"/api/v1/admin/organizations/{org_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "disabled"},
        )

    assert 201 == org_response.status_code
    assert 201 == role_response.status_code
    assert 201 == account_response.status_code
    assert 200 == edit_response.status_code
    assert "客服值班主管" == edit_response.json()["display_name"]
    assert 200 == lock_response.status_code
    assert "locked" == lock_response.json()["status"]
    assert 204 == reset_response.status_code
    assert 200 == org_disable_response.status_code
    assert "disabled" == org_disable_response.json()["status"]


@pytest.mark.anyio
async def test_city_admin_cannot_create_hq_scoped_role() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        token = await _login(client, "ops_admin")
        response = await client.post(
            "/api/v1/admin/roles",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "code": "finance",
                "name": "总部财务",
                "menus": ["dashboard"],
                "buttons": [],
                "data_scope": {"type": "all"},
            },
        )

    assert 403 == response.status_code
    assert "无权限" == response.json()["detail"]
