"""
PACK TE: Life Roles & Capacity Engine Tests
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


def test_create_role_and_capacity():
    """Test creating a life role and recording capacity."""
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Create a life role
    role_response = client.post(
        "/life/roles",
        json={
            "name": "Father",
            "domain": "family",
            "description": "Caring for and raising my children",
            "priority": 5,
        },
    )
    assert role_response.status_code == 200
    role_data = role_response.json()
    assert role_data["name"] == "Father"
    assert role_data["priority"] == 5
    role_id = role_data["id"]

    # Record a capacity snapshot
    capacity_response = client.post(
        "/life/roles/capacity",
        json={
            "role_id": role_id,
            "load_level": 0.85,
            "notes": "Kids in school, mostly managing okay",
        },
    )
    assert capacity_response.status_code == 200
    capacity_data = capacity_response.json()
    assert capacity_data["load_level"] == 0.85
    assert capacity_data["role_id"] == role_id

    # Get capacity history
    history_response = client.get(f"/life/roles/{role_id}/capacity")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert len(history_data) == 1
    assert history_data[0]["load_level"] == 0.85
