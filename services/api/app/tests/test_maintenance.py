"""
PACK UE: Maintenance Tests
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_maintenance_window_create(client):
    """Test create maintenance window"""
    start = datetime.utcnow()
    end = start + timedelta(hours=2)
    
    s = client.post(
        "/system/maintenance/windows",
        json={
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat(),
            "description": "Scheduled DB maintenance",
        },
    )
    assert s.status_code == 200
    assert s.json()["description"] == "Scheduled DB maintenance"


def test_maintenance_window_invalid(client):
    """Test maintenance window with invalid times"""
    start = datetime.utcnow()
    end = start - timedelta(hours=1)
    
    s = client.post(
        "/system/maintenance/windows",
        json={
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat(),
        },
    )
    assert s.status_code == 400


def test_maintenance_list_windows(client):
    """Test list maintenance windows"""
    start = datetime.utcnow()
    end = start + timedelta(hours=1)
    
    client.post(
        "/system/maintenance/windows",
        json={
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat(),
        },
    )
    
    r = client.get("/system/maintenance/windows")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body


def test_maintenance_state_get(client):
    """Test get maintenance state"""
    r = client.get("/system/maintenance/state")
    assert r.status_code == 200
    body = r.json()
    assert "mode" in body
    assert body["mode"] in {"normal", "maintenance", "read_only"}


def test_maintenance_state_set(client):
    """Test set maintenance state"""
    s = client.post(
        "/system/maintenance/state/maintenance",
        params={"reason": "Emergency maintenance"},
    )
    assert s.status_code == 200
    assert s.json()["mode"] == "maintenance"
    assert s.json()["reason"] == "Emergency maintenance"

    # Reset to normal
    n = client.post("/system/maintenance/state/normal")
    assert n.status_code == 200
    assert n.json()["mode"] == "normal"


def test_maintenance_state_invalid_mode(client):
    """Test invalid maintenance mode"""
    s = client.post("/system/maintenance/state/invalid_mode")
    assert s.status_code == 400
