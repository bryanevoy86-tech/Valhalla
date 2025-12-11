"""
PACK TF: System Tune List Engine Tests
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


def test_create_area_and_items():
    """Test creating tune areas and items."""
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Create a tune area
    area_response = client.post(
        "/system/tune/areas",
        json={
            "name": "Backend API",
            "description": "FastAPI endpoints and service layer",
        },
    )
    assert area_response.status_code == 200
    area_data = area_response.json()
    assert area_data["name"] == "Backend API"
    area_id = area_data["id"]

    # Create a tune item
    item_response = client.post(
        f"/system/tune/areas/{area_id}/items",
        json={
            "title": "Add retry logic to resilience endpoints",
            "description": "Implement exponential backoff",
            "priority": 3,
            "status": "pending",
        },
    )
    assert item_response.status_code == 200
    item_data = item_response.json()
    assert item_data["title"] == "Add retry logic to resilience endpoints"
    assert item_data["status"] == "pending"
    item_id = item_data["id"]

    # Mark item as in progress
    progress_response = client.post(f"/system/tune/items/{item_id}/status/in_progress")
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "in_progress"

    # Mark item as done
    done_response = client.post(f"/system/tune/items/{item_id}/status/done")
    assert done_response.status_code == 200
    done_data = done_response.json()
    assert done_data["status"] == "done"
    assert done_data["completed_at"] is not None
