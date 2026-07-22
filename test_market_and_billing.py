import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_market_symbols_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/market/symbols")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_users_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/admin/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_billing_checkout_requires_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/billing/checkout-session?plan=pro")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_rate_limited_after_repeated_bad_attempts():
    """The 6th login attempt within a minute should be rate-limited (5/minute)."""
    transport = ASGITransport(app=app)
    payload = {"email": "nonexistent@example.com", "password": "wrong-password"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        statuses = []
        for _ in range(6):
            response = await client.post("/api/v1/auth/login", json=payload)
            statuses.append(response.status_code)
    assert 429 in statuses
