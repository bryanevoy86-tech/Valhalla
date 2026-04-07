"""
PACK AM: Data Lineage Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


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


def test_record_lineage():
    payload = {
        "entity_type": "deal",
        "entity_id": "deal_123",
        "action": "created",
        "source": "user",
        "description": "Deal created via manual entry",
        "metadata": {"amount": 50000},
    }
    res = client.post("/lineage/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["entity_type"] == "deal"
    assert body["entity_id"] == "deal_123"
    assert body["action"] == "created"
    assert body["source"] == "user"


def test_record_lineage_minimal():
    payload = {
        "entity_type": "task",
        "entity_id": "task_456",
        "action": "updated",
    }
    res = client.post("/lineage/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["entity_type"] == "task"
    assert body["action"] == "updated"
    assert body["source"] is None
    assert body["metadata"] == {}


def test_list_lineage_for_entity():
    # Record multiple lineage events
    for i in range(3):
        payload = {
            "entity_type": "deal",
            "entity_id": "deal_789",
            "action": f"action_{i}",
            "source": "heimdall",
        }
        client.post("/lineage/", json=payload)

    res = client.get("/lineage/?entity_type=deal&entity_id=deal_789")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 3


def test_list_lineage_empty():
    res = client.get("/lineage/?entity_type=deal&entity_id=nonexistent")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 0


def test_list_lineage_ordering():
    """Most recent lineage should appear first."""
    for i in range(3):
        payload = {
            "entity_type": "property",
            "entity_id": "prop_999",
            "action": f"action_{i}",
        }
        client.post("/lineage/", json=payload)

    res = client.get("/lineage/?entity_type=property&entity_id=prop_999")
    assert res.status_code == 200
    body = res.json()
    # Should be DESC order (most recent first)
    assert body[0]["action"] == "action_2"
    assert body[-1]["action"] == "action_0"


def test_list_lineage_limit():
    # Record 10 lineage events
    for i in range(10):
        payload = {
            "entity_type": "child",
            "entity_id": "child_001",
            "action": f"update_{i}",
        }
        client.post("/lineage/", json=payload)

    # Default limit is 50
    res = client.get("/lineage/?entity_type=child&entity_id=child_001")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 10

    # Custom limit
    res_limited = client.get("/lineage/?entity_type=child&entity_id=child_001&limit=5")
    assert res_limited.status_code == 200
    assert len(res_limited.json()) == 5


def test_lineage_with_metadata():
    payload = {
        "entity_type": "deal",
        "entity_id": "deal_metadata",
        "action": "status_changed",
        "source": "automation",
        "metadata": {
            "old_status": "lead",
            "new_status": "under_contract",
            "changed_at": "2025-12-05T10:00:00Z",
        },
    }
    res = client.post("/lineage/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["metadata"]["new_status"] == "under_contract"
    assert body["metadata"]["old_status"] == "lead"


def test_lineage_entity_isolation():
    """Lineage for different entities should not mix."""
    # Record for entity A
    payload_a = {
        "entity_type": "deal",
        "entity_id": "deal_a",
        "action": "created",
    }
    client.post("/lineage/", json=payload_a)

    # Record for entity B
    payload_b = {
        "entity_type": "deal",
        "entity_id": "deal_b",
        "action": "updated",
    }
    client.post("/lineage/", json=payload_b)

    # Query entity A should only return A's records
    res = client.get("/lineage/?entity_type=deal&entity_id=deal_a")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["entity_id"] == "deal_a"


def test_lineage_action_sources():
    """Record lineage from different sources."""
    sources = ["user", "heimdall", "system", "automation"]
    for source in sources:
        payload = {
            "entity_type": "task",
            "entity_id": "task_multi",
            "action": "modified",
            "source": source,
        }
        client.post("/lineage/", json=payload)

    res = client.get("/lineage/?entity_type=task&entity_id=task_multi")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == len(sources)
    recorded_sources = [r["source"] for r in body]
    assert all(s in recorded_sources for s in sources)
