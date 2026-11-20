"""Real PostgreSQL integration: legacy work, owner approval and durable receipt.

Runs ONLY against a disposable CI PostgreSQL database named valhalla_factory_ci.
Never point FACTORY_TEST_POSTGRES_URL at a Render, staging or production DB.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import types
import unittest

url = os.environ.get("FACTORY_TEST_POSTGRES_URL", "")
if url and not url.endswith("/valhalla_factory_ci"):
    raise RuntimeError("Refusing to run Factory integration against a non-CI database")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/api"))
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALHALLA_JWT_SECRET", "CI-only-not-production")
models_pkg = types.ModuleType("app.models")
models_pkg.__path__ = [str(ROOT / "services/api/app/models")]
sys.modules["app.models"] = models_pkg

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.db import get_db  # noqa: E402
from app.models.completion_registry import (  # noqa: E402
    LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent,
)
from app.models.media_engine import MediaContent  # noqa: E402
from app.routers.prime_business_factory import router  # noqa: E402
from app.services.prime_business_execution import run_one_approved_draft  # noqa: E402

KEY = "ci-only-factory-test-key"
HEADERS = {"X-Business-Factory-Key": KEY}
TABLES = [
    LegacyInstanceRegistryItem,
    LegacyInstanceWorkItem,
    LegacyOrchestrationEvent,
    MediaContent,
]


@unittest.skipUnless(url, "Disposable Postgres database is not configured")
class FactoryPostgresTests(unittest.TestCase):
    def setUp(self):
        self._prior = os.environ.get("VALHALLA_FACTORY_KEY")
        os.environ["VALHALLA_FACTORY_KEY"] = KEY
        self.engine = create_engine(url, pool_pre_ping=True)
        for model in TABLES:
            model.__table__.create(bind=self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        api = FastAPI()
        api.include_router(router)

        def db_session():
            db = self.sessions()
            try:
                yield db
            finally:
                db.close()

        api.dependency_overrides[get_db] = db_session
        self.client = TestClient(api)
        session = self.sessions()
        session.add(LegacyInstanceRegistryItem(
            legacy_instance_id="ci_legacy_a",
            display_name="Disposable CI test legacy",
            assigned_businesses_json=json.dumps(["ci_business_a"]),
            assigned_jurisdictions_json=json.dumps(["CA-MB"]),
            local_knowledge_context_json=json.dumps({
                "business_id": "ci_business_a",
                "jurisdiction": "CA-MB",
                "data_namespace": "ci/legacy_a",
            }),
            engines_json=json.dumps(["ci_products"]),
            synchronization_status="SYNCED",
            isolation_state="ISOLATED",
            failover_state="NOT_TRIGGERED",
            status="PARTIAL",
        ))
        session.commit()
        session.close()
        self.payload = {
            "legacy_instance_id": "ci_legacy_a",
            "business_id": "ci_business_a",
            "industry": "digital_products",
            "jurisdiction": "CA-MB",
            "engine_id": "ci_products",
            "product_id": "ci_contractor_kit",
            "title": "Contractor Quote and Invoice Profit Kit",
            "description": "An internal test-only listing that must never be publicly posted or sold.",
            "price_cents_cad": 1900,
            "request_key": "ci-postgres-unique-request-key",
        }

    def tearDown(self):
        self.client.close()
        for model in reversed(TABLES):
            model.__table__.drop(bind=self.engine, checkfirst=True)
        self.engine.dispose()
        if self._prior is None:
            os.environ.pop("VALHALLA_FACTORY_KEY", None)
        else:
            os.environ["VALHALLA_FACTORY_KEY"] = self._prior

    def queue_and_approve(self):
        submission = self.client.post(
            "/api/business-factory/listing-drafts", headers=HEADERS, json=self.payload
        )
        self.assertEqual(submission.status_code, 200, submission.text)
        action_id = submission.json()["action_id"]
        approval = self.client.post(
            f"/api/business-factory/actions/{action_id}/approve", headers=HEADERS,
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"},
        )
        self.assertEqual(approval.status_code, 200, approval.text)
        return action_id

    def test_real_postgres_task_is_persistent_and_verifiable_on_new_session(self):
        action_id = self.queue_and_approve()
        # Simulates worker restart by obtaining an entirely new DB session.
        worker_db = self.sessions()
        try:
            result = run_one_approved_draft(worker_db)
        finally:
            worker_db.close()
        self.assertEqual(result["status"], "completed", result)
        self.assertTrue(result["verified"])
        self.assertEqual(result["receipt"]["external_effects"], 0)
        self.assertFalse(result["receipt"]["sales_verified"])

        inspected = self.client.get(
            f"/api/business-factory/actions/{action_id}", headers=HEADERS
        )
        self.assertEqual(inspected.status_code, 200, inspected.text)
        self.assertTrue(inspected.json()["internal_artifact_verified"])
        self.assertFalse(inspected.json()["payment_verified"])
        session = self.sessions()
        try:
            self.assertEqual(session.query(MediaContent).count(), 1)
            self.assertEqual(session.query(LegacyInstanceWorkItem).count(), 1)
            self.assertEqual(
                session.query(LegacyOrchestrationEvent).filter_by(
                    event_type="FACTORY_ARTIFACT_VERIFIED"
                ).count(), 1
            )
        finally:
            session.close()

    def test_two_concurrent_workers_cannot_complete_same_task_twice(self):
        action_id = self.queue_and_approve()
        barrier = threading.Barrier(2)
        results = []
        errors = []
        mutex = threading.Lock()

        def worker():
            db = self.sessions()
            try:
                barrier.wait(timeout=5)
                answer = run_one_approved_draft(db)
                with mutex:
                    results.append(answer)
            except Exception as exc:
                with mutex:
                    errors.append(type(exc).__name__)
            finally:
                db.close()

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertFalse(any(t.is_alive() for t in threads), "workers deadlocked")
        self.assertFalse(errors, errors)
        self.assertEqual(sum(r["status"] == "completed" for r in results), 1, results)
        session = self.sessions()
        try:
            self.assertEqual(session.query(MediaContent).count(), 1)
            self.assertEqual(
                session.query(LegacyOrchestrationEvent).filter_by(
                    event_type="FACTORY_ARTIFACT_VERIFIED"
                ).count(), 1
            )
            self.assertEqual(
                session.query(LegacyInstanceWorkItem).filter_by(
                    action_id=action_id
                ).one().status,
                "completed",
            )
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
