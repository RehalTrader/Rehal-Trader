import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_rejects_short_password():
    transport = ASGITransport(app=app)
    payload = {"email": "user@example.com", "full_name": "Test User", "password": "short"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422  # pydantic min_length validation


@pytest.mark.asyncio
async def test_signals_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/signals/")
    assert response.status_code == 401
