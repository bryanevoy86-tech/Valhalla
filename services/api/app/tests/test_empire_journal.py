"""
PACK AS: Empire Journal Engine Tests
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


def test_create_journal_entry():
    payload = {
        "entity_type": "deal",
        "entity_id": "123",
        "category": "insight",
        "author": "bryan",
        "title": "First note",
        "body": "This is a test journal entry.",
    }
    res = client.post("/journal/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["entity_type"] == "deal"
    assert body["category"] == "insight"


def test_list_journal_entries():
    # Create multiple entries
    for i in range(3):
        client.post(
            "/journal/",
            json={
                "entity_type": "deal",
                "entity_id": f"deal_{i}",
                "category": "note",
                "author": "lanna",
                "body": f"Entry {i}",
            },
        )

    res = client.get("/journal/")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_filter_entries_by_entity():
    # Create entries for different entities
    client.post(
        "/journal/",
        json={
            "entity_type": "deal",
            "entity_id": "deal_x",
            "category": "insight",
            "body": "Deal insight",
        },
    )
    client.post(
        "/journal/",
        json={
            "entity_type": "property",
            "entity_id": "prop_y",
            "category": "lesson",
            "body": "Property lesson",
        },
    )

    res = client.get("/journal/", params={"entity_type": "deal"})
    assert res.status_code == 200
    body = res.json()
    assert all(e["entity_type"] == "deal" for e in body)


def test_filter_entries_by_category():
    client.post(
        "/journal/",
        json={
            "category": "risk",
            "body": "Risk warning",
        },
    )
    client.post(
        "/journal/",
        json={
            "category": "win",
            "body": "Big win",
        },
    )

    res = client.get("/journal/", params={"category": "risk"})
    assert res.status_code == 200
    body = res.json()
    assert all(e["category"] == "risk" for e in body)


def test_filter_entries_by_author():
    client.post(
        "/journal/",
        json={
            "author": "heimdall",
            "category": "note",
            "body": "Heimdall observation",
        },
    )
    client.post(
        "/journal/",
        json={
            "author": "lanna",
            "category": "note",
            "body": "Lanna thought",
        },
    )

    res = client.get("/journal/", params={"author": "heimdall"})
    assert res.status_code == 200
    body = res.json()
    assert all(e["author"] == "heimdall" for e in body)


def test_entries_ordered_by_created_at():
    client.post("/journal/", json={"category": "note", "body": "First"})
    client.post("/journal/", json={"category": "note", "body": "Second"})
    client.post("/journal/", json={"category": "note", "body": "Third"})

    res = client.get("/journal/")
    body = res.json()
    # Most recent first
    assert body[0]["body"] == "Third"
    assert body[1]["body"] == "Second"
    assert body[2]["body"] == "First"
