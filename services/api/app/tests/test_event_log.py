"""
PACK AH: Event Log / Timeline Engine Tests
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


def test_record_event(client):
    """Test recording a single event"""
    payload = {
        "entity_type": "deal",
        "entity_id": "123",
        "event_type": "deal_status_changed",
        "source": "heimdall",
        "title": "Deal moved to under contract",
        "description": "Automatic status update from contract system",
    }
    res = client.post("/events/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["entity_type"] == "deal"
    assert data["entity_id"] == "123"
    assert data["event_type"] == "deal_status_changed"


def test_list_events_for_entity(client):
    """Test listing events for a specific entity"""
    # Record multiple events for same deal
    for i in range(3):
        client.post(
            "/events/",
            json={
                "entity_type": "deal",
                "entity_id": "456",
                "event_type": f"status_change_{i}",
                "source": "system",
            },
        )

    # List events for that deal
    res = client.get("/events/entity", params={"entity_type": "deal", "entity_id": "456"})
    assert res.status_code == 200
    events = res.json()
    assert len(events) == 3
    assert all(e["entity_id"] == "456" for e in events)


def test_list_events_by_entity_type_only(client):
    """Test listing all events for an entity type (not filtered by ID)"""
    # Record events for different deals
    client.post(
        "/events/",
        json={
            "entity_type": "deal",
            "entity_id": "1",
            "event_type": "created",
        },
    )
    client.post(
        "/events/",
        json={
            "entity_type": "deal",
            "entity_id": "2",
            "event_type": "created",
        },
    )
    client.post(
        "/events/",
        json={
            "entity_type": "property",
            "entity_id": "p1",
            "event_type": "created",
        },
    )

    # List all deal events
    res = client.get("/events/entity", params={"entity_type": "deal"})
    assert res.status_code == 200
    events = res.json()
    assert len(events) == 2
    assert all(e["entity_type"] == "deal" for e in events)


def test_list_recent_events(client):
    """Test listing recent events across all entities"""
    # Record events for different entity types
    client.post(
        "/events/",
        json={
            "entity_type": "deal",
            "entity_id": "1",
            "event_type": "created",
        },
    )
    client.post(
        "/events/",
        json={
            "entity_type": "property",
            "entity_id": "p1",
            "event_type": "created",
        },
    )
    client.post(
        "/events/",
        json={
            "entity_type": "child",
            "entity_id": "c1",
            "event_type": "enrolled",
        },
    )

    # List recent events
    res = client.get("/events/recent")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 3


def test_event_log_ordering(client):
    """Test that events are returned in descending order (newest first)"""
    # Record three events
    for i in range(3):
        client.post(
            "/events/",
            json={
                "entity_type": "deal",
                "entity_id": "999",
                "event_type": f"event_{i}",
            },
        )

    # List events
    res = client.get("/events/entity", params={"entity_type": "deal", "entity_id": "999"})
    events = res.json()

    # Newest should be first
    assert events[0]["event_type"] == "event_2"
    assert events[1]["event_type"] == "event_1"
    assert events[2]["event_type"] == "event_0"


def test_event_with_minimal_fields(client):
    """Test recording event with only required fields"""
    payload = {
        "entity_type": "audit",
        "event_type": "audit_started",
    }
    res = client.post("/events/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["entity_type"] == "audit"
    assert data["event_type"] == "audit_started"
    assert data["entity_id"] is None
    assert data["source"] is None


def test_limit_parameter(client):
    """Test limit parameter on entity events"""
    # Record 10 events
    for i in range(10):
        client.post(
            "/events/",
            json={
                "entity_type": "deal",
                "entity_id": "big",
                "event_type": f"event_{i}",
            },
        )

    # Get with limit
    res = client.get("/events/entity", params={"entity_type": "deal", "entity_id": "big", "limit": 3})
    assert res.status_code == 200
    events = res.json()
    assert len(events) == 3


def test_different_event_sources(client):
    """Test recording events from different sources"""
    sources = ["system", "heimdall", "user", "va", "worker"]
    for source in sources:
        client.post(
            "/events/",
            json={
                "entity_type": "deal",
                "entity_id": "multi",
                "event_type": "status_change",
                "source": source,
            },
        )

    # All should be recorded
    res = client.get("/events/entity", params={"entity_type": "deal", "entity_id": "multi"})
    events = res.json()
    assert len(events) == 5
    recorded_sources = {e["source"] for e in events}
    assert recorded_sources == set(sources)


def test_event_timestamps(client):
    """Test that events have created_at timestamp"""
    res = client.post(
        "/events/",
        json={
            "entity_type": "test",
            "event_type": "timestamp_test",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["created_at"] is not None
    assert isinstance(data["created_at"], str)  # ISO format timestamp
