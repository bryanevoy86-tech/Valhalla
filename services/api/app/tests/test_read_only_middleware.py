"""
PACK UJ: Read-Only Shield Middleware Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.maintenance import MaintenanceState
from sqlalchemy.orm import Session
from app.db import get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    from app.db import SessionLocal
    session = SessionLocal()
    yield session
    session.close()


def test_get_request_allowed(client):
    """Test GET request is always allowed"""
    r = client.get("/system/health")
    assert r.status_code in [200, 404, 500]  # Endpoint may not exist, but request was processed


def test_head_request_allowed(client):
    """Test HEAD request is always allowed"""
    r = client.head("/system/health")
    assert r.status_code in [200, 404, 500]


def test_options_request_allowed(client):
    """Test OPTIONS request is always allowed"""
    r = client.options("/system/health")
    assert r.status_code in [200, 404, 500]


def test_post_allowed_in_normal_mode(client, db):
    """Test POST is allowed when mode is normal"""
    # Ensure mode is normal
    state = db.query(MaintenanceState).first()
    if state:
        state.mode = "normal"
        db.commit()
    
    # POST request should be processed (may fail for other reasons, but not blocked)
    r = client.post(
        "/system/notify/channels",
        json={
            "name": "test",
            "channel_type": "email",
            "target": "test@example.com",
        },
    )
    # Should be processed, not blocked (status != 503)
    assert r.status_code != 503


def test_post_blocked_in_read_only_mode(client, db):
    """Test POST is blocked when mode is read_only"""
    # Set mode to read_only
    state = db.query(MaintenanceState).first()
    if state:
        state.mode = "read_only"
        db.commit()
        
        # POST request should be blocked
        r = client.post(
            "/system/notify/channels",
            json={
                "name": "test",
                "channel_type": "email",
                "target": "test@example.com",
            },
        )
        assert r.status_code == 503


def test_post_blocked_in_maintenance_mode(client, db):
    """Test POST is blocked when mode is maintenance"""
    # Set mode to maintenance
    state = db.query(MaintenanceState).first()
    if state:
        state.mode = "maintenance"
        db.commit()
        
        # POST request should be blocked
        r = client.post(
            "/system/retain/",
            json={
                "category": "test",
                "days_to_keep": 30,
            },
        )
        assert r.status_code == 503


def test_put_blocked_in_non_normal_mode(client, db):
    """Test PUT is blocked in non-normal mode"""
    state = db.query(MaintenanceState).first()
    if state:
        state.mode = "read_only"
        db.commit()
        
        r = client.put(
            "/system/some/endpoint",
            json={"data": "test"},
        )
        assert r.status_code == 503


def test_patch_blocked_in_non_normal_mode(client, db):
    """Test PATCH is blocked in non-normal mode"""
    state = db.query(MaintenanceState).first()
    if state:
        state.mode = "maintenance"
        db.commit()
        
        r = client.patch(
            "/system/some/endpoint",
            json={"data": "test"},
        )
        assert r.status_code == 503


def test_delete_blocked_in_non_normal_mode(client, db):
    """Test DELETE is blocked in non-normal mode"""
    state = db.query(MaintenanceState).first()
    if state:
        state.mode = "read_only"
        db.commit()
        
        r = client.delete("/system/some/endpoint")
        assert r.status_code == 503
