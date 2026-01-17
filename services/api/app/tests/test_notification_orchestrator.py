"""
PACK AG: Notification Orchestrator Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.db import get_db
from app.models.base import Base


@pytest.fixture
def db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client(db: Session):
    """FastAPI test client with in-memory database"""
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_channel(client):
    """Test creating a notification channel"""
    payload = {
        "key": "email",
        "name": "Email",
        "description": "Email notifications",
    }
    res = client.post("/notifications/channels", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == "email"
    assert data["is_active"] is True


def test_list_channels(client):
    """Test listing notification channels"""
    # Create a channel
    client.post("/notifications/channels", json={"key": "sms", "name": "SMS"})

    # List channels
    res = client.get("/notifications/channels")
    assert res.status_code == 200
    channels = res.json()
    assert len(channels) >= 1


def test_update_channel(client):
    """Test updating a channel"""
    # Create a channel
    res = client.post("/notifications/channels", json={"key": "push", "name": "Push"})
    channel_id = res.json()["id"]

    # Update it
    update_payload = {"is_active": False}
    res = client.patch(f"/notifications/channels/{channel_id}", json=update_payload)
    assert res.status_code == 200
    assert res.json()["is_active"] is False


def test_create_template(client):
    """Test creating a notification template"""
    payload = {
        "key": "deal_status_update",
        "channel_key": "email",
        "subject": "Deal {{deal_id}} Status Update",
        "body": "Deal {{deal_id}} is now {{status}}.",
    }
    res = client.post("/notifications/templates", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == "deal_status_update"
    assert "{{deal_id}}" in data["body"]


def test_get_template_by_key(client):
    """Test getting a template by key"""
    # Create a template
    payload = {
        "key": "user_welcome",
        "channel_key": "email",
        "subject": "Welcome {{user_name}}!",
        "body": "Welcome to Valhalla!",
    }
    client.post("/notifications/templates", json=payload)

    # Get by key
    res = client.get("/notifications/templates/user_welcome")
    assert res.status_code == 200
    assert res.json()["key"] == "user_welcome"


def test_get_nonexistent_template(client):
    """Test getting a non-existent template returns 404"""
    res = client.get("/notifications/templates/nonexistent")
    assert res.status_code == 404


def test_send_notification_success(client):
    """Test sending a notification with template rendering"""
    # Create channel
    client.post("/notifications/channels", json={"key": "email", "name": "Email"})

    # Create template
    client.post(
        "/notifications/templates",
        json={
            "key": "deal_status_update",
            "channel_key": "email",
            "subject": "Deal {{deal_id}} Status",
            "body": "Deal {{deal_id}} is now {{status}}.",
        },
    )

    # Send notification
    res = client.post(
        "/notifications/send",
        json={
            "template_key": "deal_status_update",
            "recipient": "user@example.com",
            "context": {"deal_id": 123, "status": "under contract"},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "123" in data["subject"]
    assert "under contract" in data["body"]
    assert data["status"] == "sent"


def test_send_notification_template_not_found(client):
    """Test sending notification with non-existent template logs failure"""
    res = client.post(
        "/notifications/send",
        json={
            "template_key": "nonexistent",
            "recipient": "user@example.com",
            "context": {},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "failed"
    assert "Template not found" in data["error_message"]


def test_list_logs_for_recipient(client):
    """Test listing notification logs for a recipient"""
    # Create and send notification
    client.post("/notifications/channels", json={"key": "email", "name": "Email"})
    client.post(
        "/notifications/templates",
        json={
            "key": "test_template",
            "channel_key": "email",
            "body": "Test body",
        },
    )
    client.post(
        "/notifications/send",
        json={
            "template_key": "test_template",
            "recipient": "alice@example.com",
            "context": {},
        },
    )

    # List logs
    res = client.get("/notifications/logs/by-recipient", params={"recipient": "alice@example.com"})
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1
    assert logs[0]["recipient"] == "alice@example.com"


def test_template_rendering_with_multiple_placeholders(client):
    """Test that template rendering handles multiple placeholders"""
    client.post("/notifications/channels", json={"key": "email", "name": "Email"})
    client.post(
        "/notifications/templates",
        json={
            "key": "complex_template",
            "channel_key": "email",
            "subject": "{{property}} - {{action}}",
            "body": "Property {{property}} in {{city}} has {{action}} at {{price}}",
        },
    )

    res = client.post(
        "/notifications/send",
        json={
            "template_key": "complex_template",
            "recipient": "investor@example.com",
            "context": {
                "property": "123 Main St",
                "action": "closed",
                "city": "Austin",
                "price": "$500k",
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "123 Main St" in data["subject"]
    assert "Austin" in data["body"]
    assert "$500k" in data["body"]


def test_channel_override_in_send(client):
    """Test channel override when sending notification"""
    client.post("/notifications/channels", json={"key": "sms", "name": "SMS"})
    client.post(
        "/notifications/templates",
        json={
            "key": "test",
            "channel_key": "email",
            "body": "Test",
        },
    )

    res = client.post(
        "/notifications/send",
        json={
            "template_key": "test",
            "channel_override": "sms",
            "recipient": "555-1234",
            "context": {},
        },
    )
    assert res.status_code == 200
    assert res.json()["channel_key"] == "sms"
