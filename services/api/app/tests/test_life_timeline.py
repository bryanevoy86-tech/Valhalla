"""
PACK TK: Life Timeline & Milestones Tests
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


def test_create_life_event():
    """Test creating a life event."""
    client = TestClient(app)

    # Create event
    res = client.post(
        "/timeline/events",
        json={"title": "Started Valhalla", "category": "business"},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Started Valhalla"

    # Create milestone
    m_res = client.post(
        "/timeline/milestones",
        json={
            "milestone_type": "start",
            "description": "Began building personal operating system",
        },
    )
    assert m_res.status_code == 200
