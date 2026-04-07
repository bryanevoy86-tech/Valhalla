"""
PACK AK: Analytics / Metrics Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_analytics_snapshot():
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    assert "holdings" in body
    assert "pipelines" in body
    assert "professionals" in body
    assert "children" in body
    assert "education" in body


def test_analytics_snapshot_holdings_structure():
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    holdings = body["holdings"]
    assert "active_count" in holdings
    assert "total_estimated_value" in holdings
    assert isinstance(holdings["active_count"], int)
    assert isinstance(holdings["total_estimated_value"], (int, float))


def test_analytics_snapshot_pipelines_structure():
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    pipelines = body["pipelines"]
    assert "wholesale_total" in pipelines
    assert "wholesale_under_contract" in pipelines
    assert "dispo_assignments_total" in pipelines
    assert all(isinstance(v, int) for v in pipelines.values())


def test_analytics_snapshot_professionals_structure():
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    professionals = body["professionals"]
    assert "retainers_total" in professionals
    assert "tasks_total" in professionals
    assert all(isinstance(v, int) for v in professionals.values())


def test_analytics_snapshot_children_structure():
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    children = body["children"]
    assert "hubs_total" in children
    assert isinstance(children["hubs_total"], int)


def test_analytics_snapshot_education_structure():
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    education = body["education"]
    assert "enrollments_total" in education
    assert isinstance(education["enrollments_total"], int)


def test_analytics_snapshot_default_values():
    """Verify default empty state returns zero counts."""
    res = client.get("/analytics/snapshot")
    assert res.status_code == 200
    body = res.json()
    
    # All count fields should default to 0 on empty db
    assert body["holdings"]["active_count"] == 0
    assert body["holdings"]["total_estimated_value"] == 0
    assert body["pipelines"]["wholesale_total"] == 0
    assert body["professionals"]["retainers_total"] == 0
    assert body["children"]["hubs_total"] == 0


def test_analytics_snapshot_idempotent():
    """Calling snapshot twice should return consistent structure."""
    res1 = client.get("/analytics/snapshot")
    res2 = client.get("/analytics/snapshot")
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json() == res2.json()
