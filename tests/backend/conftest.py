from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.application import app


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Provides an asynchronous test client for FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
