"""
PACK AL: Brain State Snapshot Tests
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


def test_create_brain_state():
    payload = {
        "label": "test snapshot",
        "created_by": "heimdall",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["label"] == "test snapshot"
    assert body["created_by"] == "heimdall"
    assert "empire_dashboard" in body
    assert "analytics_snapshot" in body
    assert "scenarios_summary" in body


def test_create_brain_state_without_label():
    payload = {
        "created_by": "user",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["label"] is None
    assert body["created_by"] == "user"


def test_create_brain_state_default_creator():
    payload = {
        "label": "auto snapshot",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["created_by"] == "heimdall"


def test_list_brain_states():
    # Create a few snapshots
    for i in range(3):
        payload = {
            "label": f"snapshot_{i}",
            "created_by": "heimdall",
        }
        client.post("/brain-state/", json=payload)

    res = client.get("/brain-state/")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_list_brain_states_ordering():
    """Most recent snapshots should be first."""
    # Create snapshots
    ids = []
    for i in range(3):
        payload = {
            "label": f"snapshot_{i}",
        }
        res = client.post("/brain-state/", json=payload)
        ids.append(res.json()["id"])

    res = client.get("/brain-state/")
    assert res.status_code == 200
    body = res.json()
    # Should be reverse order (most recent first)
    assert body[0]["id"] == ids[-1]
    assert body[-1]["id"] == ids[0]


def test_list_brain_states_limit():
    # Create 30 snapshots
    for i in range(30):
        payload = {"label": f"snapshot_{i}"}
        client.post("/brain-state/", json=payload)

    # Default limit is 20
    res = client.get("/brain-state/")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 20


def test_list_brain_states_custom_limit():
    # Create 10 snapshots
    for i in range(10):
        payload = {"label": f"snapshot_{i}"}
        client.post("/brain-state/", json=payload)

    # Request 5
    res = client.get("/brain-state/?limit=5")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 5


def test_brain_state_contains_empire_dashboard():
    payload = {
        "label": "test",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "empire_dashboard" in body
    assert isinstance(body["empire_dashboard"], dict)


def test_brain_state_contains_analytics_snapshot():
    payload = {
        "label": "test",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "analytics_snapshot" in body
    assert isinstance(body["analytics_snapshot"], dict)
    # Should contain expected keys from analytics
    assert "holdings" in body["analytics_snapshot"]
    assert "pipelines" in body["analytics_snapshot"]


def test_brain_state_contains_scenarios_summary():
    payload = {
        "label": "test",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "scenarios_summary" in body
    assert isinstance(body["scenarios_summary"], dict)
    assert "recent_runs" in body["scenarios_summary"]


def test_brain_state_timestamp_included():
    payload = {
        "label": "test",
    }
    res = client.post("/brain-state/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert "created_at" in body
    # Should be ISO format string
    assert isinstance(body["created_at"], str)
    assert "T" in body["created_at"]


def test_brain_state_idempotent_read():
    payload = {"label": "test"}
    res1 = client.post("/brain-state/", json=payload)
    snap_id = res1.json()["id"]

    # List and verify contents don't change
    res2 = client.get("/brain-state/")
    body2 = res2.json()
    
    res3 = client.get("/brain-state/")
    body3 = res3.json()
    
    assert body2 == body3
