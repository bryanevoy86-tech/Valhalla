"""
PACK TI: Financial Stress Early Warning Tests
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


def test_create_indicator_and_event():
    """Test creating a financial stress indicator and recording events."""
    client = TestClient(app)

    # Create indicator
    i_res = client.post(
        "/finance/stress/indicators",
        json={
            "name": "Low buffer",
            "category": "cashflow",
            "threshold_type": "below",
            "threshold_value": 1000.0,
        },
    )
    assert i_res.status_code == 200
    indicator_id = i_res.json()["id"]

    # Record stress event
    e_res = client.post(
        "/finance/stress/events",
        json={"indicator_id": indicator_id, "value_at_trigger": 500.0},
    )
    assert e_res.status_code == 200
    event_data = e_res.json()
    assert event_data["resolved"] is False

    # Resolve event
    resolve_res = client.post(f"/finance/stress/events/{event_data['id']}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["resolved"] is True
