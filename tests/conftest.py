"""
Pytest Configuration and Fixtures
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
def api_key():
    """Default API key for testing."""
    return "scuderie-dev-key-2024"


@pytest.fixture
def auth_headers(api_key):
    """Headers with API key for authenticated requests."""
    return {"X-API-Key": api_key}


@pytest.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
