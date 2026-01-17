"""
PACK UI: Data Retention Policy Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_set_retention_policy(client):
    """Test set data retention policy"""
    s = client.post(
        "/system/retention/",
        json={
            "category": "audit_logs",
            "days_to_keep": 365,
            "description": "Keep audit logs for 1 year",
        },
    )
    assert s.status_code == 200
    assert s.json()["category"] == "audit_logs"
    assert s.json()["days_to_keep"] == 365


def test_set_retention_disabled(client):
    """Test set retention policy with disabled flag"""
    s = client.post(
        "/system/retention/",
        json={
            "category": "temp_data",
            "days_to_keep": 30,
            "enabled": False,
            "description": "Temporary data (disabled for now)",
        },
    )
    assert s.status_code == 200
    assert s.json()["enabled"] is False


def test_list_retention_policies(client):
    """Test list all retention policies"""
    # Set a policy first
    client.post(
        "/system/retention/",
        json={
            "category": "logs",
            "days_to_keep": 90,
        },
    )
    
    r = client.get("/system/retention/")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body


def test_get_retention_policy_by_category(client):
    """Test get specific retention policy"""
    # Set a policy
    client.post(
        "/system/retention/",
        json={
            "category": "events",
            "days_to_keep": 60,
        },
    )
    
    # Get by category
    r = client.get("/system/retention/events")
    assert r.status_code == 200
    assert r.json()["category"] == "events"
    assert r.json()["days_to_keep"] == 60


def test_update_retention_policy(client):
    """Test update existing retention policy"""
    # Create policy
    client.post(
        "/system/retention/",
        json={
            "category": "metrics",
            "days_to_keep": 30,
        },
    )
    
    # Update it
    u = client.post(
        "/system/retention/",
        json={
            "category": "metrics",
            "days_to_keep": 180,
            "description": "Updated retention window",
        },
    )
    assert u.status_code == 200
    assert u.json()["days_to_keep"] == 180


def test_retention_policy_not_found(client):
    """Test get non-existent retention policy"""
    r = client.get("/system/retention/nonexistent_category")
    assert r.status_code == 404
