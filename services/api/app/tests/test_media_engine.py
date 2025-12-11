"""
PACK AC: Media Engine Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.db import get_db
from app.models.base import Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_media.db"
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


def test_create_media_channel(client_fixture):
    payload = {
        "name": "YouTube",
        "slug": "youtube",
        "description": "Main video channel",
    }
    res = client_fixture.post("/media/channels", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "YouTube"
    assert body["is_active"] is True


def test_list_media_channels(client_fixture):
    client_fixture.post("/media/channels", json={"name": "YouTube", "slug": "youtube"})
    client_fixture.post("/media/channels", json={"name": "Blog", "slug": "blog"})

    res = client_fixture.get("/media/channels")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_filter_channels_active_only(client_fixture):
    client_fixture.post("/media/channels", json={"name": "Active", "slug": "active"})
    ch_res = client_fixture.post(
        "/media/channels", json={"name": "Inactive", "slug": "inactive"}
    )
    channel_id = ch_res.json()["id"]

    # deactivate one
    client_fixture.patch(f"/media/channels/{channel_id}", json={"is_active": False})

    res = client_fixture.get("/media/channels?active_only=true")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1


def test_update_media_channel(client_fixture):
    c_res = client_fixture.post(
        "/media/channels", json={"name": "Old", "slug": "old"}
    )
    channel_id = c_res.json()["id"]

    u_res = client_fixture.patch(
        f"/media/channels/{channel_id}",
        json={"name": "New Name"},
    )
    assert u_res.status_code == 200
    assert u_res.json()["name"] == "New Name"


def test_create_media_content(client_fixture):
    payload = {
        "title": "Valhalla Intro",
        "content_type": "video_script",
        "body": "Here is the script...",
        "tags": "intro,valhalla",
        "audience": "public",
    }
    res = client_fixture.post("/media/content", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Valhalla Intro"
    assert body["content_type"] == "video_script"


def test_list_media_content(client_fixture):
    client_fixture.post(
        "/media/content",
        json={
            "title": "Article 1",
            "content_type": "article",
            "body": "Body 1",
        },
    )
    client_fixture.post(
        "/media/content",
        json={
            "title": "Script 1",
            "content_type": "video_script",
            "body": "Body 2",
        },
    )

    res = client_fixture.get("/media/content")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_filter_content_by_type(client_fixture):
    client_fixture.post(
        "/media/content",
        json={
            "title": "Article",
            "content_type": "article",
            "body": "Body",
        },
    )
    client_fixture.post(
        "/media/content",
        json={
            "title": "Script",
            "content_type": "video_script",
            "body": "Body",
        },
    )

    res = client_fixture.get("/media/content?content_type=article")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["content_type"] == "article"


def test_get_media_content(client_fixture):
    c_res = client_fixture.post(
        "/media/content",
        json={
            "title": "Test Content",
            "content_type": "post",
            "body": "Test body",
        },
    )
    content_id = c_res.json()["id"]

    res = client_fixture.get(f"/media/content/{content_id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == content_id
    assert body["title"] == "Test Content"


def test_create_publish_entry(client_fixture):
    # setup channel + content
    ch = client_fixture.post("/media/channels", json={"name": "Blog", "slug": "blog"}).json()
    cont = client_fixture.post(
        "/media/content",
        json={
            "title": "Blog Post 1",
            "content_type": "article",
            "body": "Body...",
        },
    ).json()

    payload = {
        "content_id": cont["id"],
        "channel_id": ch["id"],
        "status": "planned",
    }
    res = client_fixture.post("/media/publish", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "planned"
    assert body["published_at"] is None


def test_publish_marks_timestamp(client_fixture):
    # setup
    ch = client_fixture.post("/media/channels", json={"name": "YouTube", "slug": "youtube"}).json()
    cont = client_fixture.post(
        "/media/content",
        json={
            "title": "Video",
            "content_type": "video_script",
            "body": "Script",
        },
    ).json()

    # publish immediately
    payload = {
        "content_id": cont["id"],
        "channel_id": ch["id"],
        "status": "published",
    }
    res = client_fixture.post("/media/publish", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "published"
    assert body["published_at"] is not None


def test_update_publish_entry_to_published(client_fixture):
    ch = client_fixture.post("/media/channels", json={"name": "Blog", "slug": "blog"}).json()
    cont = client_fixture.post(
        "/media/content",
        json={"title": "Post", "content_type": "article", "body": "Body"},
    ).json()

    p_res = client_fixture.post(
        "/media/publish",
        json={
            "content_id": cont["id"],
            "channel_id": ch["id"],
            "status": "planned",
        },
    ).json()

    # update to published
    u_res = client_fixture.patch(
        f"/media/publish/{p_res['id']}",
        json={"status": "published"},
    )
    assert u_res.status_code == 200
    body = u_res.json()
    assert body["status"] == "published"
    assert body["published_at"] is not None


def test_add_external_ref(client_fixture):
    ch = client_fixture.post("/media/channels", json={"name": "YouTube", "slug": "youtube"}).json()
    cont = client_fixture.post(
        "/media/content",
        json={"title": "Video", "content_type": "video_script", "body": "Script"},
    ).json()

    p_res = client_fixture.post(
        "/media/publish",
        json={"content_id": cont["id"], "channel_id": ch["id"]},
    ).json()

    # add external ref
    u_res = client_fixture.patch(
        f"/media/publish/{p_res['id']}",
        json={"external_ref": "https://youtube.com/watch?v=abc123"},
    )
    assert u_res.status_code == 200
    assert u_res.json()["external_ref"] == "https://youtube.com/watch?v=abc123"


def test_list_publish_entries_for_content(client_fixture):
    ch1 = client_fixture.post(
        "/media/channels", json={"name": "YouTube", "slug": "youtube"}
    ).json()
    ch2 = client_fixture.post("/media/channels", json={"name": "Blog", "slug": "blog"}).json()
    cont = client_fixture.post(
        "/media/content",
        json={"title": "Reusable Content", "content_type": "script", "body": "Body"},
    ).json()

    # publish to both channels
    client_fixture.post(
        "/media/publish",
        json={"content_id": cont["id"], "channel_id": ch1["id"]},
    )
    client_fixture.post(
        "/media/publish",
        json={"content_id": cont["id"], "channel_id": ch2["id"]},
    )

    res = client_fixture.get(f"/media/publish/by-content/{cont['id']}")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2


def test_get_nonexistent_content(client_fixture):
    res = client_fixture.get("/media/content/999")
    assert res.status_code == 404
