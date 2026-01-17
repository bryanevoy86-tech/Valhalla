"""
PACK TD: Resilience & Recovery Planner Tests
"""

import pytest
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


def test_create_setback_and_recovery():
    """Test creating a setback event and recovery plan."""
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Create a setback event
    setback_response = client.post(
        "/resilience/setbacks",
        json={
            "title": "Job loss",
            "category": "financial",
            "description": "Lost my job unexpectedly",
            "severity": 4,
        },
    )
    assert setback_response.status_code == 200
    setback_data = setback_response.json()
    assert setback_data["title"] == "Job loss"
    assert setback_data["resolved"] is False
    setback_id = setback_data["id"]

    # Create a recovery plan
    plan_response = client.post(
        "/resilience/plans",
        json={
            "setback_id": setback_id,
            "name": "Career Transition Plan",
            "goal": "Find meaningful work within 3 months",
        },
    )
    assert plan_response.status_code == 200
    plan_data = plan_response.json()
    assert plan_data["name"] == "Career Transition Plan"
    assert plan_data["status"] == "active"
    plan_id = plan_data["id"]

    # Add a recovery action
    action_response = client.post(
        f"/resilience/plans/{plan_id}/actions",
        json={
            "description": "Update resume and LinkedIn profile",
            "order": 1,
        },
    )
    assert action_response.status_code == 200
    action_data = action_response.json()
    assert action_data["description"] == "Update resume and LinkedIn profile"
    assert action_data["completed"] is False

    # Mark action as completed
    complete_response = client.post(f"/resilience/actions/{action_data['id']}/complete")
    assert complete_response.status_code == 200
    assert complete_response.json()["completed"] is True

    # Mark setback as resolved
    resolve_response = client.post(f"/resilience/setbacks/{setback_id}/resolve")
    assert resolve_response.status_code == 200
    assert resolve_response.json()["resolved"] is True
