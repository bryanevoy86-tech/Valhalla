"""
PACK SA: Grant Eligibility Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base, get_db
from app.main import app
from app.models.grant_eligibility import GrantProfile, EligibilityChecklist

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


def test_create_grant_profile():
    """Test creating a grant profile."""
    response = client.post(
        "/grants/profiles",
        json={
            "grant_id": "grant_001",
            "program_name": "Small Business Development",
            "description": "Federal grant for startups",
            "funding_type": "grant",
            "region": "US",
            "target_groups": ["startup", "business_growth"],
            "status": "not_started",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["grant_id"] == "grant_001"
    assert data["program_name"] == "Small Business Development"


def test_get_grant_profile():
    """Test retrieving a grant profile."""
    client.post(
        "/grants/profiles",
        json={
            "grant_id": "grant_002",
            "program_name": "Training Grant",
            "funding_type": "training",
        },
    )
    response = client.get("/grants/profiles/grant_002")
    assert response.status_code == 200
    data = response.json()
    assert data["program_name"] == "Training Grant"


def test_list_grant_profiles():
    """Test listing all grant profiles."""
    client.post(
        "/grants/profiles",
        json={"grant_id": "grant_003", "program_name": "Loan Program", "funding_type": "loan"},
    )
    response = client.get("/grants/profiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_create_checklist_item():
    """Test adding a requirement to a checklist."""
    profile_response = client.post(
        "/grants/profiles",
        json={
            "grant_id": "grant_004",
            "program_name": "Business Grant",
            "funding_type": "grant",
        },
    )
    grant_id = profile_response.json()["id"]

    response = client.post(
        "/grants/checklists",
        json={
            "grant_profile_id": grant_id,
            "requirement_key": "tax_id",
            "requirement_name": "Federal Tax ID",
            "requirement_type": "document",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requirement_name"] == "Federal Tax ID"


def test_get_checklist_status():
    """Test getting checklist status/progress."""
    profile_response = client.post(
        "/grants/profiles",
        json={
            "grant_id": "grant_005",
            "program_name": "Status Test Grant",
            "funding_type": "grant",
        },
    )
    grant_id = profile_response.json()["id"]

    response = client.get(f"/grants/status/{grant_id}")
    assert response.status_code == 200
    data = response.json()
    assert "progress_percentage" in data
    assert "total_requirements" in data


def test_mark_requirement_completed():
    """Test marking a requirement as completed."""
    profile_response = client.post(
        "/grants/profiles",
        json={
            "grant_id": "grant_006",
            "program_name": "Completion Test",
            "funding_type": "grant",
        },
    )
    grant_id = profile_response.json()["id"]

    checklist_response = client.post(
        "/grants/checklists",
        json={
            "grant_profile_id": grant_id,
            "requirement_key": "business_plan",
            "requirement_name": "Business Plan",
            "requirement_type": "document",
        },
    )
    item_id = checklist_response.json()["id"]

    response = client.post(f"/grants/checklists/{item_id}/complete?uploaded=true")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
