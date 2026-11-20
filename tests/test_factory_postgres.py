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
WORKER_HEADERS = {"X-Business-Factory-Key": KEY}
HEADERS = dict(WORKER_HEADERS, **{"X-Owner-Mandate-Key": "ci-owner-only-mandate"})
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
        self._prior_owner_key = os.environ.get("VALHALLA_OWNER_MANDATE_KEY")
        os.environ["VALHALLA_OWNER_MANDATE_KEY"] = HEADERS["X-Owner-Mandate-Key"]
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
        if self._prior_owner_key is None:
            os.environ.pop("VALHALLA_OWNER_MANDATE_KEY", None)
        else:
            os.environ["VALHALLA_OWNER_MANDATE_KEY"] = self._prior_owner_key
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


    def _race_same_request(self, conflicting):
        from unittest.mock import patch
        from fastapi import HTTPException
        from app.routers.prime_business_factory import ListingDraftRequest
        from app.services import prime_business_execution as factory

        barrier = threading.Barrier(2)
        mutex = threading.Lock()
        results, errors = [], []
        original = factory._check_legacy

        def checked(*args, **kwargs):
            row = original(*args, **kwargs)
            # Both transactions have passed their initial missing-key lookup.
            barrier.wait(timeout=5)
            return row

        def submit(index):
            args = dict(self.payload)
            if conflicting and index == 1:
                args["price_cents_cad"] += 100
            with self.sessions() as db:
                try:
                    result = factory.submit_listing_draft(db, ListingDraftRequest(**args))
                    with mutex:
                        results.append(result)
                except HTTPException as exc:
                    with mutex:
                        errors.append(exc.status_code)
                except Exception as exc:
                    with mutex:
                        errors.append(type(exc).__name__)

        with patch.object(factory, "_check_legacy", side_effect=checked):
            threads = [threading.Thread(target=submit, args=(i,)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)
        self.assertFalse(any(t.is_alive() for t in threads), "concurrent submission stalled")
        self.assertEqual(errors, [409] if conflicting else [])
        self.assertEqual(len(results), 1 if conflicting else 2)
        self.assertEqual(sum(not r["duplicate"] for r in results), 1)
        self.assertEqual(len({r["action_id"] for r in results}), 1)
        with self.sessions() as db:
            self.assertEqual(db.query(LegacyInstanceWorkItem).count(), 1)
            self.assertEqual(db.query(LegacyOrchestrationEvent).filter_by(
                event_type="FACTORY_WORK_QUEUED").count(), 1)
            self.assertEqual(db.query(MediaContent).count(), 0)

    def test_concurrent_identical_submit_reconciles_unique_key_race(self):
        self._race_same_request(conflicting=False)

    def test_concurrent_different_submit_rejects_conflicting_request(self):
        self._race_same_request(conflicting=True)

    def test_two_workers_share_one_standing_mandate_cap(self):
        grant = {k: self.payload[k] for k in (
            "legacy_instance_id", "business_id", "engine_id", "jurisdiction", "product_id"
        )}
        grant.update(mandate_id="ci-one-use-mandate", ttl_seconds=3600,
                     max_uses=1, max_price_cents_cad=2000)
        response = self.client.post("/api/business-factory/mandates", json=grant, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        for i in range(2):
            payload = dict(self.payload, mandate_id=grant["mandate_id"], request_key=f"ci-mandate-job-{i}")
            submitted = self.client.post("/api/business-factory/listing-drafts",
                                         json=payload, headers=WORKER_HEADERS)
            self.assertEqual(submitted.status_code, 200, submitted.text)

        barrier = threading.Barrier(2)
        results, errors = [], []
        mutex = threading.Lock()

        def worker():
            with self.sessions() as db:
                try:
                    barrier.wait(timeout=5)
                    result = run_one_approved_draft(db)
                    with mutex:
                        results.append(result)
                except Exception as exc:
                    with mutex:
                        errors.append(type(exc).__name__)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        self.assertFalse(any(t.is_alive() for t in threads))
        self.assertFalse(errors, errors)
        self.assertEqual(sum(r["status"] == "completed" for r in results), 1, results)
        with self.sessions() as db:
            self.assertEqual(run_one_approved_draft(db)["reason"], "MANDATE_EXHAUSTED")
            self.assertEqual(db.query(MediaContent).count(), 1)
            self.assertEqual(db.query(LegacyInstanceWorkItem).filter_by(status="completed").count(), 1)


if __name__ == "__main__":
    unittest.main()
