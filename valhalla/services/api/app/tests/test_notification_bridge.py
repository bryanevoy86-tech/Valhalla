"""
PACK AJ: Notification Bridge Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base
from app.models.event_log import EventLog
from app.models.notification_bridge import NotificationPreference


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_preference():
    pref_payload = {
        "user_id": 1,
        "entity_type": "deal",
        "event_type": "deal_status_changed",
        "channel_key": "email",
        "template_key": "deal_status_update",
    }
    res = client.post("/notification-bridge/preferences", json=pref_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["user_id"] == 1
    assert body["event_type"] == "deal_status_changed"
    assert body["is_enabled"] is True


def test_list_preferences_for_user():
    pref_payload = {
        "user_id": 1,
        "entity_type": "deal",
        "event_type": "deal_status_changed",
        "channel_key": "email",
        "template_key": "deal_status_update",
    }
    client.post("/notification-bridge/preferences", json=pref_payload)

    res = client.get("/notification-bridge/preferences/by-user/1")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    assert body[0]["user_id"] == 1


def test_list_preferences_empty():
    res = client.get("/notification-bridge/preferences/by-user/999")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 0


def test_update_preference():
    pref_payload = {
        "user_id": 1,
        "entity_type": "deal",
        "event_type": "deal_status_changed",
        "channel_key": "email",
        "template_key": "deal_status_update",
    }
    res = client.post("/notification-bridge/preferences", json=pref_payload)
    pref_id = res.json()["id"]

    update_payload = {
        "channel_key": "sms",
        "is_enabled": False,
    }
    update_res = client.patch(f"/notification-bridge/preferences/{pref_id}", json=update_payload)
    assert update_res.status_code == 200
    body = update_res.json()
    assert body["channel_key"] == "sms"
    assert body["is_enabled"] is False


def test_update_nonexistent_preference():
    update_payload = {"channel_key": "sms"}
    res = client.patch("/notification-bridge/preferences/999", json=update_payload)
    assert res.status_code == 404


def test_create_pref_and_dispatch():
    # Create a preference
    pref_payload = {
        "user_id": 1,
        "entity_type": "deal",
        "event_type": "deal_status_changed",
        "channel_key": "email",
        "template_key": "deal_status_update",
    }
    res = client.post("/notification-bridge/preferences", json=pref_payload)
    assert res.status_code == 200

    # Create an event
    ev_payload = {
        "entity_type": "deal",
        "entity_id": "123",
        "event_type": "deal_status_changed",
        "source": "heimdall",
        "title": "Deal 123 moved",
    }
    ev_res = client.post("/events/", json=ev_payload)
    assert ev_res.status_code == 200
    event_id = ev_res.json()["id"]

    # Dispatch notifications
    d_res = client.post(
        f"/notification-bridge/dispatch/{event_id}",
        params=[("user_ids", 1)]
    )
    assert d_res.status_code == 200
    body = d_res.json()
    assert body["event_id"] == event_id
    assert body["notifications_created"] >= 0


def test_dispatch_nonexistent_event():
    res = client.post(
        "/notification-bridge/dispatch/999",
        params=[("user_ids", 1)]
    )
    assert res.status_code == 404


def test_preference_disabled_no_dispatch():
    # Create a disabled preference
    pref_payload = {
        "user_id": 2,
        "entity_type": "property",
        "event_type": "property_added",
        "channel_key": "sms",
        "template_key": "property_new",
        "is_enabled": False,
    }
    pref_res = client.post("/notification-bridge/preferences", json=pref_payload)
    pref_id = pref_res.json()["id"]

    # Create matching event
    ev_payload = {
        "entity_type": "property",
        "entity_id": "prop_456",
        "event_type": "property_added",
        "source": "user",
        "title": "New property added",
    }
    ev_res = client.post("/events/", json=ev_payload)
    event_id = ev_res.json()["id"]

    # Dispatch should not send (preference disabled)
    d_res = client.post(
        f"/notification-bridge/dispatch/{event_id}",
        params=[("user_ids", 2)]
    )
    assert d_res.status_code == 200
    body = d_res.json()
    assert body["notifications_created"] == 0


def test_multiple_users_dispatch():
    # Create preferences for multiple users
    for uid in [1, 2]:
        pref_payload = {
            "user_id": uid,
            "entity_type": "deal",
            "event_type": "deal_closed",
            "channel_key": "email",
            "template_key": "deal_closed_alert",
        }
        client.post("/notification-bridge/preferences", json=pref_payload)

    # Create event
    ev_payload = {
        "entity_type": "deal",
        "entity_id": "deal_789",
        "event_type": "deal_closed",
        "source": "worker",
        "title": "Deal closed",
    }
    ev_res = client.post("/events/", json=ev_payload)
    event_id = ev_res.json()["id"]

    # Dispatch to multiple users
    d_res = client.post(
        f"/notification-bridge/dispatch/{event_id}",
        params=[("user_ids", 1), ("user_ids", 2)]
    )
    assert d_res.status_code == 200
    body = d_res.json()
    assert body["notifications_created"] >= 2
    assert 1 in body["recipients"]
    assert 2 in body["recipients"]


def test_entity_type_wildcard_matching():
    # Create preference with no entity_type (matches all)
    pref_payload = {
        "user_id": 3,
        "entity_type": None,
        "event_type": "generic_event",
        "channel_key": "in_app",
        "template_key": "generic_alert",
    }
    client.post("/notification-bridge/preferences", json=pref_payload)

    # Create event with specific entity_type
    ev_payload = {
        "entity_type": "any_entity",
        "entity_id": "id_999",
        "event_type": "generic_event",
        "source": "system",
        "title": "Generic event",
    }
    ev_res = client.post("/events/", json=ev_payload)
    event_id = ev_res.json()["id"]

    # Dispatch should match despite different entity_type
    d_res = client.post(
        f"/notification-bridge/dispatch/{event_id}",
        params=[("user_ids", 3)]
    )
    assert d_res.status_code == 200
    body = d_res.json()
    assert body["notifications_created"] >= 1
