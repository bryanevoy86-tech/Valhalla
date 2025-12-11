"""
PACK TJ: Kids Education & Development Tests
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


def test_create_child_and_learning_plan():
    """Test creating a child profile and learning plan."""
    client = TestClient(app)

    # Create child
    c_res = client.post("/kids/children", json={"name": "Archer", "age": 7})
    assert c_res.status_code == 200
    child_id = c_res.json()["id"]

    # Create learning plan
    p_res = client.post(
        "/kids/learning-plans",
        json={
            "child_id": child_id,
            "timeframe": "weekly",
            "goals": "Read 3 chapters\nPractice math",
        },
    )
    assert p_res.status_code == 200
    plan_data = p_res.json()
    assert plan_data["timeframe"] == "weekly"

    # Create education log
    log_res = client.post(
        "/kids/logs",
        json={
            "child_id": child_id,
            "completed_activities": "Read chapter 1 and 2",
            "highlights": "Really enjoyed the story",
        },
    )
    assert log_res.status_code == 200
