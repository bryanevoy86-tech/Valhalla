"""
PACK UF: Admin Ops Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_admin_ops_get_maintenance_state(client):
    """Test admin ops get maintenance state"""
    s = client.post(
        "/admin/ops/",
        json={
            "action": "get_maintenance_state",
        },
    )
    assert s.status_code == 200
    body = s.json()
    assert body["ok"] is True
    assert "data" in body
    assert "mode" in body["data"]


def test_admin_ops_set_maintenance_mode(client):
    """Test admin ops set maintenance mode"""
    s = client.post(
        "/admin/ops/",
        json={
            "action": "set_maintenance_mode",
            "payload": {
                "mode": "read_only",
                "reason": "Admin-triggered read-only mode",
            },
        },
    )
    assert s.status_code == 200
    body = s.json()
    assert body["ok"] is True
    assert body["data"]["mode"] == "read_only"

    # Reset
    client.post(
        "/admin/ops/",
        json={
            "action": "set_maintenance_mode",
            "payload": {"mode": "normal"},
        },
    )


def test_admin_ops_set_feature_flag(client):
    """Test admin ops set feature flag"""
    s = client.post(
        "/admin/ops/",
        json={
            "action": "set_feature_flag",
            "payload": {
                "key": "admin_test_flag",
                "enabled": True,
                "group": "testing",
            },
        },
    )
    assert s.status_code == 200
    body = s.json()
    assert body["ok"] is True
    assert body["data"]["flag"]["key"] == "admin_test_flag"


def test_admin_ops_deployment_profile(client):
    """Test admin ops get deployment profile"""
    s = client.post(
        "/admin/ops/",
        json={
            "action": "deployment_profile",
            "payload": {"environment": "prod"},
        },
    )
    assert s.status_code == 200
    body = s.json()
    assert body["ok"] is True
    assert "profile" in body["data"]
    assert body["data"]["profile"]["environment"] == "prod"


def test_admin_ops_unknown_action(client):
    """Test admin ops with unknown action"""
    s = client.post(
        "/admin/ops/",
        json={
            "action": "unknown_action",
        },
    )
    assert s.status_code == 200
    body = s.json()
    assert body["ok"] is False
    assert "Unknown admin action" in body["detail"]
