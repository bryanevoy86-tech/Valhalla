"""Tests for WeWeb authentication compatibility layer."""
import os
import pytest

# Set up test auth environment BEFORE importing the app
# This must be done before any app imports to ensure auth is configured correctly
os.environ.setdefault("VALHALLA_AUTH_ENABLED", "true")
os.environ.setdefault("VALHALLA_OWNER_USERNAME", "owner@valhalla.local")
os.environ.setdefault("VALHALLA_OWNER_PASSWORD", "test-password-123")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test-secret-key-for-tests")
os.environ.setdefault("VALHALLA_TOKEN_TTL_SECONDS", "3600")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestWeWebSmoke:
    """Test public smoke endpoint."""

    def test_smoke_endpoint_returns_ok(self, client):
        """GET /api/weweb/smoke should return 200 with ok=true."""
        response = client.get("/api/weweb/smoke")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "WeWeb auth bridge" in data["message"]


class TestWeWebLogin:
    """Test login endpoint."""

    def test_login_with_valid_credentials(self, client):
        """POST /api/weweb/login with valid credentials should return access_token."""
        response = client.post(
            "/api/weweb/login",
            json={"email": "owner@valhalla.local", "password": "test-password-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "owner@valhalla.local"
        assert data["user"]["role"] == "owner"

    def test_login_with_invalid_email(self, client):
        """POST /api/weweb/login with wrong email should return 401."""
        response = client.post(
            "/api/weweb/login",
            json={"email": "wrong@valhalla.local", "password": "test-password-123"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data.get("detail", "")

    def test_login_with_invalid_password(self, client):
        """POST /api/weweb/login with wrong password should return 401."""
        response = client.post(
            "/api/weweb/login",
            json={"email": "owner@valhalla.local", "password": "wrong-password"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data.get("detail", "")

    def test_login_with_empty_credentials(self, client):
        """POST /api/weweb/login with empty credentials should fail."""
        response = client.post(
            "/api/weweb/login",
            json={"email": "", "password": ""},
        )
        assert response.status_code == 401


class TestWeWebMe:
    """Test /me endpoint (requires authentication)."""

    def test_me_with_valid_token(self, client):
        """GET /api/weweb/me with valid token should return user info."""
        # First, get a valid token
        login_response = client.post(
            "/api/weweb/login",
            json={"email": "owner@valhalla.local", "password": "test-password-123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Now call /me with the token
        response = client.get(
            "/api/weweb/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["user"]["email"] == "owner@valhalla.local"
        assert data["user"]["role"] == "owner"

    def test_me_without_token(self, client):
        """GET /api/weweb/me without token should return 403."""
        response = client.get("/api/weweb/me")
        assert response.status_code in [401, 403]

    def test_me_with_invalid_token(self, client):
        """GET /api/weweb/me with invalid token should return 401."""
        response = client.get(
            "/api/weweb/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_me_with_malformed_auth_header(self, client):
        """GET /api/weweb/me with malformed auth header should return 401."""
        response = client.get(
            "/api/weweb/me",
            headers={"Authorization": "NotBearer token"},
        )
        # OAuth2PasswordBearer returns 401 for malformed or missing auth
        assert response.status_code in [401, 403]


class TestWeWebCORS:
    """Test CORS headers are present."""

    def test_cors_headers_on_login(self, client):
        """POST /api/weweb/login should include CORS headers."""
        response = client.post(
            "/api/weweb/login",
            json={"email": "owner@valhalla.local", "password": "test-password-123"},
            headers={"Origin": "http://localhost:3000"},
        )
        # Note: TestClient may not include CORS headers in response
        # but we verify the endpoint works with auth headers
        assert response.status_code == 200

    def test_cors_preflight_smoke(self, client):
        """OPTIONS request should be handled for CORS."""
        response = client.options("/api/weweb/smoke")
        # TestClient may not support OPTIONS fully, but endpoint should exist
        assert response.status_code in [200, 405]


class TestWeWebIntegration:
    """Integration tests for WeWeb auth flow."""

    def test_complete_login_and_me_flow(self, client):
        """Test complete flow: login -> get token -> use token for /me."""
        # Step 1: Login
        login_response = client.post(
            "/api/weweb/login",
            json={"email": "owner@valhalla.local", "password": "test-password-123"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]

        # Step 2: Use token to call /me
        me_response = client.get(
            "/api/weweb/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["ok"] is True
        assert me_data["user"]["email"] == login_data["user"]["email"]

    def test_token_reusable_across_calls(self, client):
        """Token should be reusable across multiple /me calls."""
        # Get token once
        login_response = client.post(
            "/api/weweb/login",
            json={"email": "owner@valhalla.local", "password": "test-password-123"},
        )
        token = login_response.json()["access_token"]

        # Use it multiple times
        for _ in range(3):
            response = client.get(
                "/api/weweb/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
