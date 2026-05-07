"""System API contract tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.anyio
async def test_healthz_returns_stable_payload_and_request_id() -> None:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/healthz", headers={"X-Request-ID": "req_test"})

    assert 200 == response.status_code
    assert "req_test" == response.headers["X-Request-ID"]
    assert {
        "status": "ok",
        "service": "rental-car-api",
        "version": "0.1.0",
    } == response.json()


@pytest.mark.anyio
async def test_api_v1_system_health_is_documented_contract() -> None:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/system/health")

    assert 200 == response.status_code
    assert "X-Request-ID" in response.headers
    assert "ok" == response.json()["status"]


@pytest.mark.anyio
async def test_openapi_contains_versioned_health_route() -> None:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/openapi.json")

    assert 200 == response.status_code
    schema = response.json()
    assert "/api/v1/system/health" in schema["paths"]
    assert "查询 API 健康状态" == schema["paths"]["/api/v1/system/health"]["get"]["summary"]

