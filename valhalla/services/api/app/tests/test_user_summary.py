"""
PACK AT: User-Facing Summary Snapshot Tests
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


def test_create_summary():
    payload = {
        "summary_type": "weekly",
        "audience": "family",
        "title": "Weekly Empire Update",
        "body": "This week, we made progress on several fronts.",
        "created_by": "heimdall",
    }
    res = client.post("/summaries/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["summary_type"] == "weekly"
    assert body["audience"] == "family"


def test_list_summaries():
    for i in range(3):
        client.post(
            "/summaries/",
            json={
                "summary_type": "daily",
                "body": f"Summary {i}",
            },
        )

    res = client.get("/summaries/")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_filter_summaries_by_type():
    client.post(
        "/summaries/",
        json={"summary_type": "weekly", "body": "Weekly update"},
    )
    client.post(
        "/summaries/",
        json={"summary_type": "monthly", "body": "Monthly update"},
    )

    res = client.get("/summaries/", params={"summary_type": "weekly"})
    assert res.status_code == 200
    body = res.json()
    assert all(s["summary_type"] == "weekly" for s in body)


def test_filter_summaries_by_audience():
    client.post(
        "/summaries/",
        json={"audience": "family", "body": "Family-friendly summary"},
    )
    client.post(
        "/summaries/",
        json={"audience": "ops", "body": "Ops summary"},
    )

    res = client.get("/summaries/", params={"audience": "family"})
    assert res.status_code == 200
    body = res.json()
    assert all(s["audience"] == "family" for s in body)


def test_summary_with_title():
    payload = {
        "summary_type": "custom",
        "title": "Q4 Empire Overview",
        "body": "Comprehensive overview of Q4 performance.",
        "created_by": "bryan",
    }
    res = client.post("/summaries/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Q4 Empire Overview"


def test_summaries_ordered_by_created_at():
    client.post("/summaries/", json={"body": "First"})
    client.post("/summaries/", json={"body": "Second"})
    client.post("/summaries/", json={"body": "Third"})

    res = client.get("/summaries/")
    body = res.json()
    # Most recent first
    assert body[0]["body"] == "Third"
    assert body[1]["body"] == "Second"
    assert body[2]["body"] == "First"
