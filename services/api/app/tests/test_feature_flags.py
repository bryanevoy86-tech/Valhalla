"""
PACK AX: Feature Flags & Experiments Tests
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


def test_create_feature_flag():
    payload = {
        "key": "kids_story_mode",
        "name": "Kids Story Mode",
        "description": "Enable story generation for kids",
        "enabled": True,
        "audience": "kids",
    }
    res = client.post("/features/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["key"] == "kids_story_mode"
    assert body["enabled"] is True


def test_get_feature_flag_by_key():
    client.post(
        "/features/",
        json={
            "key": "test_flag",
            "name": "Test Flag",
            "enabled": False,
        },
    )

    res = client.get("/features/test_flag")
    assert res.status_code == 200
    body = res.json()
    assert body["key"] == "test_flag"


def test_get_nonexistent_flag():
    res = client.get("/features/nonexistent_flag")
    assert res.status_code == 404


def test_update_feature_flag():
    p_res = client.post(
        "/features/",
        json={
            "key": "feature_1",
            "name": "Feature 1",
            "enabled": False,
        },
    )
    flag_id = p_res.json()["id"]

    u_res = client.patch(
        f"/features/{flag_id}",
        json={"enabled": True, "audience": "founders"},
    )
    assert u_res.status_code == 200
    body = u_res.json()
    assert body["enabled"] is True
    assert body["audience"] == "founders"


def test_update_nonexistent_flag():
    res = client.patch(
        "/features/999",
        json={"enabled": True},
    )
    assert res.status_code == 404


def test_list_all_feature_flags():
    for i in range(3):
        client.post(
            "/features/",
            json={
                "key": f"flag_{i}",
                "name": f"Flag {i}",
            },
        )

    res = client.get("/features/")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_filter_flags_by_audience():
    client.post(
        "/features/",
        json={
            "key": "kids_flag",
            "name": "Kids Flag",
            "audience": "kids",
        },
    )
    client.post(
        "/features/",
        json={
            "key": "global_flag",
            "name": "Global Flag",
            "audience": "global",
        },
    )
    client.post(
        "/features/",
        json={
            "key": "ops_flag",
            "name": "Ops Flag",
            "audience": "ops",
        },
    )

    # Get kids audience should include kids + global
    res = client.get("/features/", params={"audience": "kids"})
    assert res.status_code == 200
    body = res.json()
    audiences = {f["audience"] for f in body}
    assert "kids" in audiences or "global" in audiences


def test_feature_flag_variants():
    payload = {
        "key": "ab_test_flag",
        "name": "A/B Test Flag",
        "enabled": True,
        "variant": "B",
    }
    res = client.post("/features/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["variant"] == "B"


def test_feature_flag_with_description():
    payload = {
        "key": "feature_with_desc",
        "name": "Feature With Description",
        "description": "This is a test feature flag",
        "enabled": True,
    }
    res = client.post("/features/", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["description"] == "This is a test feature flag"
