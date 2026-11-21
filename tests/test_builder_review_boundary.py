"""Exercise real Builder HTTP/ORM contracts in an isolated temp repository."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "services/api"
sys.path.insert(0, str(API))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALHALLA_JWT_SECRET", "ci-only-not-production")

# Use actual Builder ORM models without unrelated historical eager imports.
pkg = types.ModuleType("app.models")
pkg.__path__ = [str(API / "app/models")]
sys.modules["app.models"] = pkg

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.db import get_db
from app.core.settings import settings
from app.models.builder import BuilderEvent, BuilderTask
from app.routers import builder

HEADERS = {"X-API-Key": "test-only-builder-key"}


class BuilderReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.path = "services/api/app/routers/base.py"
        self.base = self.root / self.path
        self.base.parent.mkdir(parents=True)
        self.base.write_text("VALUE = 1\n", encoding="utf-8")
        for target, key, value in [(builder, "_REPO_ROOT", self.root),
                                   (settings, "BUILDER_KEY", HEADERS["X-API-Key"]),
                                   (settings, "BUILDER_ALLOWED_DIRS", ["services/api/app/routers"])]:
            context = patch.object(target, key, value)
            context.start()
            self.addCleanup(context.stop)
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.addCleanup(self.engine.dispose)
        for model in (BuilderTask, BuilderEvent):
            model.__table__.create(bind=self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        app = FastAPI()
        app.include_router(builder.router)

        def session():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = session
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        response = self.client.post("/builder/tasks", headers=HEADERS,
            json={"title": "Test isolated change", "scope": "internal-test"})
        self.assertEqual(response.status_code, 200, response.text)
        self.task = response.json()["task_id"]
        self.proposal = [{"path": self.path, "mode": "replace", "content": "VALUE = 2\n"}]

    def draft(self, files=None):
        return self.client.post(f"/builder/draft?task_id={self.task}", headers=HEADERS,
                                json=self.proposal if files is None else files)

    def prepare(self):
        return self.client.post("/builder/apply", headers=HEADERS,
                                json={"task_id": self.task, "approve": False})

    def export(self):
        return self.client.get(f"/builder/tasks/{self.task}/review-bundle", headers=HEADERS)

    def test_review_bundle_survives_fresh_session_without_source_writes(self):
        draft = self.draft()
        self.assertEqual(draft.status_code, 200, draft.text)
        self.assertFalse(draft.json()["tests_verified"])
        self.assertEqual(self.export().status_code, 409)
        prepared = self.prepare()
        self.assertEqual(prepared.status_code, 200, prepared.text)
        bundle = self.export()
        self.assertEqual(bundle.status_code, 200, bundle.text)
        self.assertEqual(bundle.json()["sha256"], draft.json()["bundle_sha256"])
        self.assertFalse(bundle.json()["source_modified"])
        self.assertFalse(bundle.json()["tests_verified"])
        self.assertFalse(bundle.json()["deployed"])
        self.assertEqual(bundle.json()["bundle"]["files"][0]["content"], "VALUE = 2\n")
        self.assertEqual(self.prepare().status_code, 200)
        with self.sessions() as db:
            self.assertEqual(db.get(BuilderTask, self.task).status, "review_ready")
            self.assertEqual(db.query(BuilderEvent).filter_by(kind="review_ready").count(), 1)
        self.assertEqual(self.base.read_text(), "VALUE = 1\n")

    def test_stale_base_blocks_review_and_export(self):
        self.assertEqual(self.draft().status_code, 200)
        self.assertEqual(self.prepare().status_code, 200)
        self.base.write_text("VALUE = 99\n", encoding="utf-8")
        self.assertEqual(self.prepare().status_code, 409)
        self.assertEqual(self.export().status_code, 409)
        self.assertEqual(self.base.read_text(), "VALUE = 99\n")

    def test_invalid_batch_cannot_replace_existing_draft(self):
        valid = self.draft()
        self.assertEqual(valid.status_code, 200, valid.text)
        duplicate = self.proposal + [dict(self.proposal[0], path=self.path.replace("/", "\\"))]
        self.assertEqual(self.draft(duplicate).status_code, 422)
        self.assertEqual(self.draft([dict(self.proposal[0], mode="add")]).status_code, 409)
        self.assertEqual(self.draft([dict(self.proposal[0], content="VALUE = 1\n")]).status_code, 422)
        self.assertEqual(self.prepare().status_code, 200)
        self.assertEqual(self.export().json()["sha256"], valid.json()["bundle_sha256"])

    def test_direct_apply_denied_even_with_builder_key(self):
        self.assertEqual(self.draft().status_code, 200)
        self.assertEqual(self.prepare().status_code, 200)
        result = self.client.post("/builder/apply", headers=HEADERS, json={"task_id": self.task, "approve": True})
        self.assertEqual(result.status_code, 409)
        self.assertEqual(self.base.read_text(), "VALUE = 1\n")
        self.assertEqual(self.client.get(f"/builder/tasks/{self.task}/review-bundle").status_code, 401)

    def test_tampered_bundle_rejected(self):
        self.assertEqual(self.draft().status_code, 200)
        with self.sessions() as db:
            task = db.get(BuilderTask, self.task)
            data = json.loads(task.payload_json)
            data["bundle"]["files"][0]["content"] = "VALUE = 999\n"
            task.payload_json = json.dumps(data)
            db.commit()
        self.assertEqual(self.prepare().status_code, 409)
        self.assertEqual(self.base.read_text(), "VALUE = 1\n")


if __name__ == "__main__":
    unittest.main()
