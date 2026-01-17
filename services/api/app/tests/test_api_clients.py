"""
PACK UD: API Clients Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_client_create(client):
    """Test create API client"""
    s = client.post(
        "/system/clients/",
        json={
            "name": "WeWeb",
            "client_type": "weweb",
            "api_key": "sk_weweb_test123",
            "description": "WeWeb frontend client",
        },
    )
    assert s.status_code == 200
    assert s.json()["name"] == "WeWeb"
    assert s.json()["active"] is True


def test_api_client_list(client):
    """Test list API clients"""
    client.post(
        "/system/clients/",
        json={
            "name": "Heimdall",
            "client_type": "heimdall",
            "api_key": "sk_heimdall_test123",
        },
    )
    
    r = client.get("/system/clients/")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body
    assert body["total"] >= 1


def test_api_client_activate(client):
    """Test activate deactivated client"""
    s = client.post(
        "/system/clients/",
        json={
            "name": "TestClient",
            "client_type": "script",
            "api_key": "sk_test_activate",
        },
    )
    client_id = s.json()["id"]

    # Deactivate
    d = client.post(f"/system/clients/{client_id}/deactivate")
    assert d.status_code == 200
    assert d.json()["active"] is False

    # Reactivate
    a = client.post(f"/system/clients/{client_id}/activate")
    assert a.status_code == 200
    assert a.json()["active"] is True


def test_api_client_deactivate(client):
    """Test deactivate client"""
    s = client.post(
        "/system/clients/",
        json={
            "name": "DisableMe",
            "client_type": "integration",
            "api_key": "sk_test_deactivate",
        },
    )
    client_id = s.json()["id"]

    d = client.post(f"/system/clients/{client_id}/deactivate")
    assert d.status_code == 200
    assert d.json()["active"] is False
