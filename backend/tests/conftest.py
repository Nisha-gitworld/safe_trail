"""
pytest conftest.py — shared fixtures for all backend tests
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app


# ── Event loop ────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── HTTP client ───────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ── Auth helpers ──────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Register a test user and return auth headers."""
    await client.post("/api/auth/register", json={
        "email":     "testuser@safetrail.test",
        "password":  "testpass123",
        "full_name": "Test Tourist",
    })
    res = await client.post("/api/auth/login", json={
        "email":    "testuser@safetrail.test",
        "password": "testpass123",
    })
    token = res.json().get("access_token", "test-token")
    return {"Authorization": f"Bearer {token}"}


# ── Sample data fixtures ──────────────────────────────────────────────────────
@pytest.fixture
def safe_location():
    return {"lat": 18.944, "lng": 72.823, "hour": 14, "speed": 1.5,
            "dwell_time": 60, "crowd_density": 0.2, "user_id": "test"}


@pytest.fixture
def danger_location():
    return {"lat": 19.040, "lng": 72.855, "hour": 23, "speed": 0.1,
            "dwell_time": 700, "crowd_density": 0.9, "user_id": "test"}
