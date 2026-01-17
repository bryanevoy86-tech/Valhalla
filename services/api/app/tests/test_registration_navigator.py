"""
PACK SB: Business Registration Navigator Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base, get_db
from app.main import app
from app.models.registration_navigator import RegistrationFlowStep, RegistrationStageTracker

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_registration_step():
    """Test creating a registration workflow step."""
    response = client.post(
        "/registration/steps",
        json={
            "step_id": "step_001",
            "category": "naming",
            "description": "Research and select your business name",
            "required_documents": [{"filename": "name_research.txt", "type": "text"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["step_id"] == "step_001"
    assert data["category"] == "naming"


def test_get_steps_by_category():
    """Test retrieving steps in a category."""
    client.post(
        "/registration/steps",
        json={
            "step_id": "step_002",
            "category": "structure",
            "description": "Select your business structure",
        },
    )
    response = client.get("/registration/steps/category/structure")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["category"] == "structure"


def test_create_tracker():
    """Test creating a new registration tracker."""
    response = client.post("/registration/tracker")
    assert response.status_code == 200
    data = response.json()
    assert data["current_stage"] == "preparation"


def test_set_business_name():
    """Test recording business name (Stage 1)."""
    tracker_response = client.post("/registration/tracker")
    tracker_id = tracker_response.json()["id"]

    response = client.post(f"/registration/tracker/{tracker_id}/business-name?name=Acme%20Corp")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"


def test_set_structure():
    """Test recording structure selection (Stage 2)."""
    tracker_response = client.post("/registration/tracker")
    tracker_id = tracker_response.json()["id"]

    response = client.post(
        f"/registration/tracker/{tracker_id}/structure?structure=corporation&notes=C-Corp%20for%20growth"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["selected_structure"] == "corporation"


def test_advance_stage():
    """Test advancing to next stage."""
    tracker_response = client.post("/registration/tracker")
    tracker_id = tracker_response.json()["id"]

    response = client.post(f"/registration/tracker/{tracker_id}/stage/structure")
    assert response.status_code == 200
    data = response.json()
    assert data["new_stage"] == "structure"


def test_get_progress():
    """Test getting registration progress."""
    tracker_response = client.post("/registration/tracker")
    tracker_id = tracker_response.json()["id"]

    response = client.get(f"/registration/tracker/{tracker_id}/progress")
    assert response.status_code == 200
    data = response.json()
    assert "current_stage" in data
    assert "progress_percentage" in data
    assert "next_stage" in data


def test_get_tracker_info():
    """Test retrieving tracker details."""
    tracker_response = client.post("/registration/tracker")
    tracker_id = tracker_response.json()["id"]

    response = client.get(f"/registration/tracker/{tracker_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["current_stage"] == "preparation"


def test_full_workflow():
    """Test a complete registration workflow."""
    # Create tracker
    tracker_response = client.post("/registration/tracker")
    tracker_id = tracker_response.json()["id"]

    # Set business name
    client.post(f"/registration/tracker/{tracker_id}/business-name?name=MyBusiness%20Inc")

    # Set structure
    client.post(f"/registration/tracker/{tracker_id}/structure?structure=corporation")

    # Check progress
    progress_response = client.get(f"/registration/tracker/{tracker_id}/progress")
    data = progress_response.json()
    assert data["current_stage"] == "preparation"  # Still in preparation
    assert len(data["missing_items"]) == 0  # Should have business name and structure
