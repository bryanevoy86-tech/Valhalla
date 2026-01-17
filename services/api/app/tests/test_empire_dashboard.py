"""
PACK AF: Unified Empire Dashboard Tests
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


def test_empire_dashboard_endpoint_structure(client):
    """Test that empire dashboard endpoint returns correct structure"""
    res = client.get("/dashboard/empire")
    assert res.status_code == 200
    body = res.json()
    
    # Verify top-level keys
    assert "system" in body
    assert "holdings" in body
    assert "pipelines" in body
    assert "risk_governance" in body
    assert "education" in body
    assert "children" in body


def test_empire_dashboard_system_section(client):
    """Test system section has required fields"""
    res = client.get("/dashboard/empire")
    body = res.json()
    system = body["system"]
    
    assert "version" in system
    assert "backend_complete" in system
    assert isinstance(system["version"], str)
    assert isinstance(system["backend_complete"], bool)


def test_empire_dashboard_holdings_section(client):
    """Test holdings section has required fields"""
    res = client.get("/dashboard/empire")
    body = res.json()
    holdings = body["holdings"]
    
    assert "count" in holdings
    assert "total_estimated_value" in holdings
    assert isinstance(holdings["count"], int)
    assert isinstance(holdings["total_estimated_value"], (int, float))


def test_empire_dashboard_pipelines_section(client):
    """Test pipelines section has required fields"""
    res = client.get("/dashboard/empire")
    body = res.json()
    pipelines = body["pipelines"]
    
    assert "wholesale_total" in pipelines
    assert "wholesale_active" in pipelines
    assert "dispo_assignments" in pipelines
    assert all(isinstance(v, int) for v in pipelines.values())


def test_empire_dashboard_risk_governance_section(client):
    """Test risk governance section has required fields"""
    res = client.get("/dashboard/empire")
    body = res.json()
    risk = body["risk_governance"]
    
    assert "open_audit_events" in risk
    assert "governance_decisions" in risk
    assert all(isinstance(v, int) for v in risk.values())


def test_empire_dashboard_education_section(client):
    """Test education section has required fields"""
    res = client.get("/dashboard/empire")
    body = res.json()
    education = body["education"]
    
    assert "enrollments_total" in education
    assert isinstance(education["enrollments_total"], int)


def test_empire_dashboard_children_section(client):
    """Test children section has required fields"""
    res = client.get("/dashboard/empire")
    body = res.json()
    children = body["children"]
    
    assert "hubs_total" in children
    assert isinstance(children["hubs_total"], int)


def test_empire_dashboard_initial_state(client):
    """Test that initial empty database returns zeroes"""
    res = client.get("/dashboard/empire")
    body = res.json()
    
    # Most counts should be 0 in empty database
    assert body["holdings"]["count"] == 0
    assert body["pipelines"]["wholesale_total"] == 0
    assert body["education"]["enrollments_total"] == 0
    assert body["children"]["hubs_total"] == 0


def test_empire_dashboard_idempotent(client):
    """Test that calling dashboard multiple times returns consistent structure"""
    res1 = client.get("/dashboard/empire")
    res2 = client.get("/dashboard/empire")
    
    assert res1.json() == res2.json()
