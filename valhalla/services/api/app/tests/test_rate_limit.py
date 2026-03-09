"""
PACK UC: Rate Limit Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rate_limit_rule_crud(client):
    """Test create and retrieve rate limit rule"""
    s = client.post(
        "/system/ratelimits/rules",
        json={
            "scope": "ip",
            "key": "192.168.1.1",
            "window_seconds": 60,
            "max_requests": 100,
            "enabled": True,
        },
    )
    assert s.status_code == 200
    assert s.json()["key"] == "192.168.1.1"
    rule_id = s.json()["id"]

    # Get rule
    r = client.get(f"/system/ratelimits/rules/{rule_id}")
    assert r.status_code == 200
    assert r.json()["max_requests"] == 100


def test_rate_limit_list(client):
    """Test list rules with scope filter"""
    client.post(
        "/system/ratelimits/rules",
        json={"scope": "user", "key": "user123", "max_requests": 50},
    )
    
    r = client.get("/system/ratelimits/rules?scope=user")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body


def test_rate_limit_delete(client):
    """Test delete rate limit rule"""
    s = client.post(
        "/system/ratelimits/rules",
        json={"scope": "api_key", "key": "test_key", "max_requests": 200},
    )
    rule_id = s.json()["id"]

    # Delete
    d = client.delete(f"/system/ratelimits/rules/{rule_id}")
    assert d.status_code == 200
    assert d.json()["deleted"] is True

    # Verify deleted
    r = client.get(f"/system/ratelimits/rules/{rule_id}")
    assert r.status_code == 404


def test_rate_limit_snapshots(client):
    """Test get rate limit snapshots"""
    r = client.get("/system/ratelimits/snapshots")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_rate_limit_snapshots_with_limit(client):
    """Test snapshots with custom limit"""
    r = client.get("/system/ratelimits/snapshots?limit=50")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
