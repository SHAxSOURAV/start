import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Verifies the root endpoint returns welcome message."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.text


@pytest.mark.asyncio
async def test_health_live_endpoint(async_client: AsyncClient) -> None:
    """Verifies the container liveness probe endpoint."""
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert "uptime" in data


@pytest.mark.asyncio
async def test_health_ready_endpoint(async_client: AsyncClient) -> None:
    """Verifies the readiness probe endpoint returns proper health structure."""
    response = await async_client.get("/health/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
