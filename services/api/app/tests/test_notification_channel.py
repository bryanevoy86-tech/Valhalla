"""
PACK UG: Notification Channel Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_notification_channel_create(client):
    """Test create notification channel"""
    s = client.post(
        "/system/notify/channels",
        json={
            "name": "owner_email",
            "channel_type": "email",
            "target": "owner@example.com",
            "description": "Owner notification email",
        },
    )
    assert s.status_code == 200
    assert s.json()["name"] == "owner_email"
    assert s.json()["active"] is True


def test_notification_channel_list(client):
    """Test list notification channels"""
    client.post(
        "/system/notify/channels",
        json={
            "name": "security_webhook",
            "channel_type": "webhook",
            "target": "https://security.example.com/alerts",
        },
    )
    
    r = client.get("/system/notify/channels")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body


def test_enqueue_notification(client):
    """Test enqueue notification"""
    # Create channel first
    channel = client.post(
        "/system/notify/channels",
        json={
            "name": "test_channel",
            "channel_type": "email",
            "target": "test@example.com",
        },
    ).json()
    
    # Enqueue notification
    s = client.post(
        "/system/notify/",
        json={
            "channel_id": channel["id"],
            "subject": "Test Alert",
            "body": "This is a test notification",
        },
    )
    assert s.status_code == 200
    assert s.json()["status"] == "pending"


def test_list_notifications(client):
    """Test list notifications"""
    r = client.get("/system/notify/")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "items" in body


def test_list_notifications_by_status(client):
    """Test list notifications filtered by status"""
    r = client.get("/system/notify/?status=pending")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["items"], list)
