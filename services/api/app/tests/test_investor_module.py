"""
PACK AE: Public Investor Module Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.db import get_db
from app.models.base import Base


@pytest.fixture
def db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client(db: Session):
    """FastAPI test client with in-memory database"""
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_investor_profile(client):
    """Test creating a new investor profile"""
    payload = {
        "user_id": 1,
        "full_name": "John Investor",
        "email": "john@example.com",
        "is_accredited": True,
        "country": "USA",
        "strategy_preference": "growth",
        "risk_tolerance": "moderate",
    }
    res = client.post("/investor/profile", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 1
    assert data["full_name"] == "John Investor"
    assert data["is_accredited"] is True


def test_get_investor_profile(client):
    """Test getting an investor profile"""
    # Create a profile
    payload = {
        "user_id": 2,
        "full_name": "Jane Investor",
        "is_accredited": False,
    }
    client.post("/investor/profile", json=payload)

    # Get the profile
    res = client.get("/investor/profile/2")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == 2
    assert data["full_name"] == "Jane Investor"


def test_get_nonexistent_profile(client):
    """Test getting a non-existent profile returns None"""
    res = client.get("/investor/profile/999")
    assert res.status_code == 200
    assert res.json() is None


def test_update_investor_profile(client):
    """Test updating an investor profile"""
    # Create a profile
    payload = {
        "user_id": 3,
        "full_name": "Bob Investor",
        "strategy_preference": "income",
    }
    client.post("/investor/profile", json=payload)

    # Update the profile
    update_payload = {
        "strategy_preference": "mixed",
        "risk_tolerance": "higher",
    }
    res = client.patch("/investor/profile/3", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["strategy_preference"] == "mixed"
    assert data["risk_tolerance"] == "higher"


def test_create_investor_project(client):
    """Test creating a project summary"""
    payload = {
        "slug": "bahamas-resort-1",
        "title": "Bahamas Resort #1",
        "region": "Bahamas",
        "description": "High-end resort development opportunity",
        "status": "research",
    }
    res = client.post("/investor/projects", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == "bahamas-resort-1"
    assert data["title"] == "Bahamas Resort #1"
    assert data["status"] == "research"


def test_list_investor_projects(client):
    """Test listing project summaries"""
    # Create multiple projects
    for i in range(3):
        payload = {
            "slug": f"project-{i}",
            "title": f"Project {i}",
            "region": "USA",
            "status": "research" if i < 2 else "open",
        }
        client.post("/investor/projects", json=payload)

    # List all projects
    res = client.get("/investor/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 3


def test_list_investor_projects_filtered_by_status(client):
    """Test filtering projects by status"""
    # Create projects with different statuses
    client.post("/investor/projects", json={"slug": "proj-1", "title": "Project 1", "status": "research"})
    client.post("/investor/projects", json={"slug": "proj-2", "title": "Project 2", "status": "open"})
    client.post("/investor/projects", json={"slug": "proj-3", "title": "Project 3", "status": "research"})

    # Filter by status
    res = client.get("/investor/projects?status=research")
    assert res.status_code == 200
    projects = res.json()
    assert all(p["status"] == "research" for p in projects)


def test_get_investor_project_by_slug(client):
    """Test getting a project by slug"""
    # Create a project
    payload = {
        "slug": "downtown-office",
        "title": "Downtown Office Complex",
        "region": "New York",
    }
    client.post("/investor/projects", json=payload)

    # Get the project
    res = client.get("/investor/projects/downtown-office")
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == "downtown-office"
    assert data["title"] == "Downtown Office Complex"


def test_get_nonexistent_project(client):
    """Test getting a non-existent project returns 404"""
    res = client.get("/investor/projects/nonexistent")
    assert res.status_code == 404


def test_update_investor_project(client):
    """Test updating a project summary"""
    # Create a project
    payload = {
        "slug": "test-project",
        "title": "Test Project",
        "status": "research",
    }
    client.post("/investor/projects", json=payload)

    # Update the project
    update_payload = {
        "title": "Test Project Updated",
        "status": "open",
    }
    res = client.patch("/investor/projects/test-project", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Project Updated"
    assert data["status"] == "open"


def test_create_profile_idempotent(client):
    """Test that creating profile with same user_id returns existing profile"""
    payload = {"user_id": 50, "full_name": "Same User"}
    res1 = client.post("/investor/profile", json=payload)
    id1 = res1.json()["id"]

    # Create again with same user_id
    res2 = client.post("/investor/profile", json=payload)
    id2 = res2.json()["id"]

    assert id1 == id2
