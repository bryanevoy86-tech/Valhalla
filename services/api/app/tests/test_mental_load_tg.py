"""
PACK TG: Mental Load Offloading Tests
"""

import pytest
from datetime import datetime
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


def test_create_and_list_mental_load_entries():
    """Test creating and listing mental load entries."""
    client = TestClient(app)

    # Create entry
    res = client.post(
        "/mental-load/entries",
        json={"category": "task", "description": "Call CRA", "urgency_level": 4},
    )
    assert res.status_code == 200
    entry_data = res.json()
    assert entry_data["category"] == "task"
    assert entry_data["archived"] is False

    # List entries
    res_list = client.get("/mental-load/entries")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Archive entry
    archive_res = client.post(f"/mental-load/entries/{entry_data['id']}/archive")
    assert archive_res.status_code == 200
    assert archive_res.json()["archived"] is True
