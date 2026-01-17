"""
PACK TL: Strategic Decision Archive Tests
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


def test_create_decision_and_revision():
    """Test creating a strategic decision and adding revisions."""
    client = TestClient(app)

    # Create decision
    d_res = client.post(
        "/decisions/",
        json={"title": "Focus on BRRRR", "category": "real_estate"},
    )
    assert d_res.status_code == 200
    decision_id = d_res.json()["id"]

    # Add revision
    r_res = client.post(
        "/decisions/revisions",
        json={
            "decision_id": decision_id,
            "reason_for_revision": "Market conditions shifted",
        },
    )
    assert r_res.status_code == 200

    # Update status
    status_res = client.post(f"/decisions/{decision_id}/status/revised")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "revised"
