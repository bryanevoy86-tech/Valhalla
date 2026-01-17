"""
PACK TH: Crisis Management Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import Base, engine, SessionLocal


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_create_crisis_profile_and_log():
    """Test creating a crisis profile and logging events."""
    client = TestClient(app)

    # Create profile
    c_res = client.post(
        "/crisis/profiles",
        json={"name": "Financial emergency", "category": "financial"},
    )
    assert c_res.status_code == 200
    crisis_id = c_res.json()["id"]

    # Create log entry
    log_res = client.post(
        "/crisis/logs",
        json={"crisis_id": crisis_id, "event": "Income dropped suddenly"},
    )
    assert log_res.status_code == 200
    log_data = log_res.json()
    assert log_data["active"] is True

    # Resolve log
    resolve_res = client.post(f"/crisis/logs/{log_data['id']}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["active"] is False
