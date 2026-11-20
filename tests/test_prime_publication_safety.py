"""Actual FastAPI/SQLAlchemy coverage for media/marketing owner gates.

Posting database records is not independently verified external publication.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "services/api"
sys.path.insert(0, str(API))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALHALLA_JWT_SECRET", "test-jwt-secret-not-production")

# Avoid eagerly importing unrelated legacy models while exercising real
# Media/Marketing service, router and SQLAlchemy model code.
pkg = types.ModuleType("app.models")
pkg.__path__ = [str(API / "app/models")]
sys.modules["app.models"] = pkg

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from app.core.db import get_db  # noqa: E402
from app.core.settings import settings  # noqa: E402
from app.models.media_engine import MediaChannel, MediaContent, MediaPublishLog  # noqa: E402
from app.models.marketing import MarketingCampaign, SocialPost  # noqa: E402
from app.routers.media_engine import router as media_router  # noqa: E402
from app.routers.marketing import router as marketing_router  # noqa: E402


HEADERS = {"X-API-Key": "test-media-owner-key"}


class PublicationSafetyTests(unittest.TestCase):
    def setUp(self):
        self.old_builder_key = settings.BUILDER_KEY
        settings.BUILDER_KEY = HEADERS["X-API-Key"]
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.session_factory = sessionmaker(bind=self.engine)
        for model in (MediaChannel, MediaContent, MediaPublishLog, MarketingCampaign, SocialPost):
            model.__table__.create(bind=self.engine)
        api = FastAPI()
        api.include_router(media_router)
        api.include_router(marketing_router)

        def provide_db():
            session = self.session_factory()
            try:
                yield session
            finally:
                session.close()

        api.dependency_overrides[get_db] = provide_db
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        settings.BUILDER_KEY = self.old_builder_key

    def test_no_owner_key_cannot_modify_or_list_media_and_marketing(self):
        self.assertEqual(self.client.get("/media/channels").status_code, 401)
        self.assertEqual(self.client.get("/marketing/campaigns").status_code, 401)
        self.assertEqual(self.client.post("/marketing/post", json={
            "platform": "youtube", "content_payload": "test", "status": "queued",
        }).status_code, 401)

    def _seed(self):
        channel = self.client.post("/media/channels", headers=HEADERS, json={
            "name": "Video", "slug": "video-test", "description": "safe only"
        })
        self.assertEqual(channel.status_code, 200, channel.text)
        content = self.client.post("/media/content", headers=HEADERS, json={
            "title": "Example", "body": "Sample non-published content",
            "content_type": "social_post", "tags": "demo", "audience": "public",
        })
        self.assertEqual(content.status_code, 200, content.text)
        return channel.json()["id"], content.json()["id"]

    def test_media_cannot_fabricate_published_status(self):
        channel_id, content_id = self._seed()
        published = self.client.post("/media/publish", headers=HEADERS, json={
            "channel_id": channel_id, "content_id": content_id,
            "status": "published", "external_ref": "made_up_remote_id",
        })
        self.assertEqual(published.status_code, 409)
        planned = self.client.post("/media/publish", headers=HEADERS, json={
            "channel_id": channel_id, "content_id": content_id,
            "status": "planned",
        })
        self.assertEqual(planned.status_code, 200, planned.text)
        update = self.client.patch(f"/media/publish/{planned.json()['id']}", headers=HEADERS, json={
            "status": "published", "external_ref": "made_up_remote_id",
        })
        self.assertEqual(update.status_code, 409)
        session = self.session_factory()
        row = session.query(MediaPublishLog).first()
        self.assertEqual(row.status, "planned")
        self.assertIsNone(row.published_at)
        session.close()

    def test_social_marketing_post_cannot_fabricate_publication(self):
        fake = self.client.post("/marketing/post", headers=HEADERS, json={
            "platform": "tiktok", "content_payload": "test", "status": "published"
        })
        self.assertEqual(fake.status_code, 409)
        queued = self.client.post("/marketing/post", headers=HEADERS, json={
            "platform": "tiktok", "content_payload": "safe draft", "status": "queued"
        })
        self.assertEqual(queued.status_code, 200, queued.text)
        update = self.client.put(f"/marketing/post/{queued.json()['id']}", headers=HEADERS, json={
            "platform": "tiktok", "content_payload": "fake external posting", "status": "published"
        })
        self.assertEqual(update.status_code, 409)
        session = self.session_factory()
        row = session.query(SocialPost).first()
        self.assertEqual(row.status, "queued")
        session.close()


if __name__ == "__main__":
    unittest.main()
