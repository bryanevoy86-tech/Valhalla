"""
PACK AV: Narrative Story Mode Tests
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


def test_create_story_prompt():
    payload = {
        "audience": "kids",
        "theme": "pizza_adventure",
        "title": "Pizza Quest",
        "prompt_text": "Heimdall helps the kids make magical pizza.",
        "created_by": "lanna",
    }
    res = client.post("/stories/prompts", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["audience"] == "kids"
    assert body["theme"] == "pizza_adventure"


def test_list_story_prompts():
    for i in range(3):
        client.post(
            "/stories/prompts",
            json={
                "audience": "kids",
                "theme": "adventure",
                "title": f"Story {i}",
                "prompt_text": f"Prompt {i}",
            },
        )

    res = client.get("/stories/prompts")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_filter_prompts_by_audience():
    client.post(
        "/stories/prompts",
        json={"audience": "kids", "prompt_text": "Kids story"},
    )
    client.post(
        "/stories/prompts",
        json={"audience": "family", "prompt_text": "Family story"},
    )

    res = client.get("/stories/prompts", params={"audience": "kids"})
    assert res.status_code == 200
    body = res.json()
    assert all(p["audience"] == "kids" for p in body)


def test_filter_prompts_by_theme():
    client.post(
        "/stories/prompts",
        json={"theme": "adventure", "prompt_text": "Adventure story"},
    )
    client.post(
        "/stories/prompts",
        json={"theme": "bedtime", "prompt_text": "Bedtime story"},
    )

    res = client.get("/stories/prompts", params={"theme": "adventure"})
    assert res.status_code == 200
    body = res.json()
    assert all(p["theme"] == "adventure" for p in body)


def test_create_story_output():
    p_res = client.post(
        "/stories/prompts",
        json={
            "audience": "kids",
            "theme": "learning",
            "prompt_text": "Learn about space",
        },
    )
    prompt_id = p_res.json()["id"]

    o_res = client.post(
        "/stories/outputs",
        json={
            "prompt_id": prompt_id,
            "audience": "kids",
            "theme": "learning",
            "title": "Space Adventure",
            "body": "Once upon a time in a galaxy far away...",
            "created_by": "heimdall",
        },
    )
    assert o_res.status_code == 200
    body = o_res.json()
    assert body["prompt_id"] == prompt_id
    assert body["created_by"] == "heimdall"


def test_list_story_outputs():
    for i in range(3):
        client.post(
            "/stories/outputs",
            json={
                "audience": "family",
                "theme": "empire",
                "body": f"Story {i}",
            },
        )

    res = client.get("/stories/outputs")
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 3


def test_filter_outputs_by_audience():
    client.post(
        "/stories/outputs",
        json={"audience": "kids", "body": "Kids story"},
    )
    client.post(
        "/stories/outputs",
        json={"audience": "ops", "body": "Ops story"},
    )

    res = client.get("/stories/outputs", params={"audience": "kids"})
    assert res.status_code == 200
    body = res.json()
    assert all(o["audience"] == "kids" for o in body)
