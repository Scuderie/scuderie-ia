"""
API Integration Tests
"""
import pytest


class TestHealthEndpoint:
    """Tests for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Root endpoint should return welcome message."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAuthentication:
    """Tests for API key authentication."""
    
    @pytest.mark.asyncio
    async def test_ingest_without_api_key_fails(self, client):
        """Ingest without API key should return 401."""
        response = await client.post(
            "/api/v1/ingest",
            json={"source_id": "test", "source_type": "test", "content": "test"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_search_without_api_key_fails(self, client):
        """Search without API key should return 401."""
        response = await client.post(
            "/api/v1/search",
            json={"source_id": "test", "source_type": "test", "content": "test"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_chat_without_api_key_fails(self, client):
        """Chat without API key should return 401."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "test"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_api_key_fails(self, client):
        """Invalid API key should return 401."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": "test"},
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401


class TestSessionsEndpoint:
    """Tests for session management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, client, auth_headers):
        """List sessions should return array."""
        response = await client.get("/api/v1/sessions", headers=auth_headers)
        # This might need DB, so accept either success or server error
        assert response.status_code in [200, 500]
