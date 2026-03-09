"""
PACK AU: Trust & Residency Profile Tests
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


def test_create_trust_profile():
    payload = {
        "subject_type": "professional",
        "subject_id": "lawyer_1",
        "country": "CA",
        "region": "AB",
        "city": "Calgary",
        "trust_score": 70.0,
        "footprint_score": 10.0,
    }
    res = client.post("/trust-residency/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["subject_type"] == "professional"
    assert body["trust_score"] == 70.0


def test_create_or_get_profile_returns_existing():
    payload = {
        "subject_type": "user",
        "subject_id": "user_1",
        "country": "US",
    }
    res1 = client.post("/trust-residency/", json=payload)
    res2 = client.post("/trust-residency/", json=payload)

    assert res1.status_code == 200
    assert res2.status_code == 200
    # Both should have same ID
    assert res1.json()["id"] == res2.json()["id"]


def test_get_profile():
    # Create profile
    client.post(
        "/trust-residency/",
        json={
            "subject_type": "vendor",
            "subject_id": "vendor_1",
            "country": "MX",
            "trust_score": 60.0,
        },
    )

    # Get profile
    res = client.get(
        "/trust-residency/",
        params={"subject_type": "vendor", "subject_id": "vendor_1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["country"] == "MX"
    assert body["trust_score"] == 60.0


def test_update_profile():
    # Create profile
    client.post(
        "/trust-residency/",
        json={
            "subject_type": "tenant",
            "subject_id": "tenant_1",
            "trust_score": 50.0,
        },
    )

    # Update profile
    res = client.patch(
        "/trust-residency/",
        params={"subject_type": "tenant", "subject_id": "tenant_1"},
        json={"trust_score": 85.0, "city": "Toronto"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["trust_score"] == 85.0
    assert body["city"] == "Toronto"


def test_get_nonexistent_profile():
    res = client.get(
        "/trust-residency/",
        params={"subject_type": "unknown", "subject_id": "unknown_1"},
    )
    assert res.status_code == 404


def test_update_nonexistent_profile():
    res = client.patch(
        "/trust-residency/",
        params={"subject_type": "unknown", "subject_id": "unknown_1"},
        json={"trust_score": 75.0},
    )
    assert res.status_code == 404


def test_list_profiles():
    for i in range(3):
        client.post(
            "/trust-residency/",
            json={
                "subject_type": "professional",
                "subject_id": f"prof_{i}",
            },
        )

    res = client.get("/trust-residency/list")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_filter_profiles_by_type():
    client.post(
        "/trust-residency/",
        json={"subject_type": "professional", "subject_id": "prof_1"},
    )
    client.post(
        "/trust-residency/",
        json={"subject_type": "vendor", "subject_id": "vendor_1"},
    )

    res = client.get(
        "/trust-residency/list", params={"subject_type": "professional"}
    )
    assert res.status_code == 200
    body = res.json()
    assert all(p["subject_type"] == "professional" for p in body)


def test_filter_profiles_by_min_trust():
    client.post(
        "/trust-residency/",
        json={"subject_type": "user", "subject_id": "user_1", "trust_score": 30.0},
    )
    client.post(
        "/trust-residency/",
        json={"subject_type": "user", "subject_id": "user_2", "trust_score": 75.0},
    )

    res = client.get("/trust-residency/list", params={"min_trust": 50.0})
    assert res.status_code == 200
    body = res.json()
    assert all(p["trust_score"] >= 50.0 for p in body)


def test_trust_score_validation():
    payload = {
        "subject_type": "test",
        "subject_id": "test_1",
        "trust_score": 150.0,  # Invalid: > 100
    }
    res = client.post("/trust-residency/", json=payload)
    assert res.status_code == 422  # Validation error


def test_footprint_score_validation():
    payload = {
        "subject_type": "test",
        "subject_id": "test_2",
        "footprint_score": -5.0,  # Invalid: < 0
    }
    res = client.post("/trust-residency/", json=payload)
    assert res.status_code == 422  # Validation error
