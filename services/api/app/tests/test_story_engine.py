"""
PACK AA: Story Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_story.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def client_fixture():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return client


def test_create_story_template(client_fixture):
    payload = {
        "arc_name": "Valhalla Chronicles",
        "audience": "child",
        "tone": "funny",
        "purpose": "bedtime",
        "prompt": "Heimdall takes the kids on a pizza quest.",
    }
    res = client_fixture.post("/stories/templates", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["arc_name"] == "Valhalla Chronicles"
    assert body["purpose"] == "bedtime"
    assert body["is_active"] is True


def test_list_story_templates(client_fixture):
    # create multiple templates
    client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Arc 1",
            "prompt": "Prompt 1",
            "purpose": "bedtime",
        },
    )
    client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Arc 2",
            "prompt": "Prompt 2",
            "purpose": "encouragement",
        },
    )

    # list all
    res = client_fixture.get("/stories/templates")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_filter_templates_by_purpose(client_fixture):
    client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Bedtime 1",
            "prompt": "Sleep",
            "purpose": "bedtime",
        },
    )
    client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Learn 1",
            "prompt": "Learn",
            "purpose": "lesson",
        },
    )

    res = client_fixture.get("/stories/templates?purpose=bedtime")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["purpose"] == "bedtime"


def test_get_story_template(client_fixture):
    t_res = client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Test Arc",
            "prompt": "Test prompt",
        },
    )
    template_id = t_res.json()["id"]

    res = client_fixture.get(f"/stories/templates/{template_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == template_id
    assert body["arc_name"] == "Test Arc"


def test_update_story_template(client_fixture):
    t_res = client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Original",
            "prompt": "Original prompt",
            "purpose": "bedtime",
        },
    )
    template_id = t_res.json()["id"]

    # update
    u_res = client_fixture.patch(
        f"/stories/templates/{template_id}",
        json={
            "arc_name": "Updated",
            "is_active": False,
        },
    )
    assert u_res.status_code == 200
    body = u_res.json()
    assert body["arc_name"] == "Updated"
    assert body["is_active"] is False


def test_create_story_episode(client_fixture):
    # make template
    t_res = client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Test Arc",
            "prompt": "Short test prompt.",
        },
    )
    template_id = t_res.json()["id"]

    ep_payload = {
        "template_id": template_id,
        "child_id": 1,
        "title": "Episode 1",
        "content": "Once upon a time...",
        "mood": "cozy",
        "length_estimate_minutes": 10,
    }
    res = client_fixture.post("/stories/episodes", json=ep_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["template_id"] == template_id
    assert body["child_id"] == 1
    assert body["content"] == "Once upon a time..."


def test_list_episodes_by_child(client_fixture):
    # create template
    t_res = client_fixture.post(
        "/stories/templates",
        json={
            "arc_name": "Test",
            "prompt": "Prompt",
        },
    )
    template_id = t_res.json()["id"]

    # create multiple episodes for same child
    client_fixture.post(
        "/stories/episodes",
        json={
            "template_id": template_id,
            "child_id": 1,
            "content": "Episode 1",
        },
    )
    client_fixture.post(
        "/stories/episodes",
        json={
            "template_id": template_id,
            "child_id": 1,
            "content": "Episode 2",
        },
    )

    res = client_fixture.get("/stories/episodes/by-child/1")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_episode_requires_template(client_fixture):
    # try to create episode with non-existent template
    res = client_fixture.post(
        "/stories/episodes",
        json={
            "template_id": 999,
            "child_id": 1,
            "content": "Test",
        },
    )
    # Should fail at database constraint level
    assert res.status_code in [400, 422]


def test_get_nonexistent_template(client_fixture):
    res = client_fixture.get("/stories/templates/999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
