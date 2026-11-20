"""Business Factory integrated persistence tests.

Uses the real FastAPI router, SQLAlchemy models, and a disposable SQLite
database. No outbound integrations, AI calls, or live Render resources.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
sys.path.insert(0, str(API_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("VALHALLA_JWT_SECRET", "local-test-only")

# The legacy app.models package eagerly imports unrelated historical modules.
# Isolate the actual ORM model files this integration uses without changing them.
pkg = types.ModuleType("app.models")
pkg.__path__ = [str(API_ROOT / "app" / "models")]
sys.modules["app.models"] = pkg

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.db import get_db  # noqa: E402
from app.models.completion_registry import (  # noqa: E402
    LegacyInstanceRegistryItem,
    LegacyInstanceWorkItem,
    LegacyOrchestrationEvent,
)
from app.models.media_engine import MediaContent  # noqa: E402
from app.routers.prime_business_factory import router  # noqa: E402


WORKER_HEADERS = {"X-Business-Factory-Key": "test-business-factory-key"}
HEADERS = dict(WORKER_HEADERS, **{"X-Owner-Mandate-Key": "ci-owner-only-mandate"})


class BusinessFactoryPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["VALHALLA_FACTORY_KEY"] = HEADERS["X-Business-Factory-Key"]
        self._prior_owner_key = os.environ.get("VALHALLA_OWNER_MANDATE_KEY")
        os.environ["VALHALLA_OWNER_MANDATE_KEY"] = HEADERS["X-Owner-Mandate-Key"]
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        for model in (
            LegacyInstanceRegistryItem,
            LegacyInstanceWorkItem,
            LegacyOrchestrationEvent,
            MediaContent,
        ):
            model.__table__.create(bind=self.engine)

        app = FastAPI()
        app.include_router(router)

        def override_db():
            session = self.sessions()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)
        self.seed_instance()
        self.payload = {
            "legacy_instance_id": "digital_product_legacy",
            "business_id": "valhalla_digital",
            "industry": "digital_products",
            "jurisdiction": "CA-MB",
            "engine_id": "digital_products",
            "product_id": "contractor_kit",
            "title": "Contractor Quote and Invoice Profit Kit",
            "description": "Downloadable calculator and worksheet bundle for preparing quotes, invoices, and job cost reports for small contractors.",
            "price_cents_cad": 1900,
            "request_key": "contractor-pilot-v1",
        }

    def tearDown(self) -> None:
        self.client.close()
        if self._prior_owner_key is None:
            os.environ.pop("VALHALLA_OWNER_MANDATE_KEY", None)
        else:
            os.environ["VALHALLA_OWNER_MANDATE_KEY"] = self._prior_owner_key
        self.engine.dispose()
        os.environ.pop("VALHALLA_FACTORY_KEY", None)

    def seed_instance(self, **overrides):
        data = {
            "legacy_instance_id": "digital_product_legacy",
            "display_name": "Digital Products",
            "assigned_businesses_json": json.dumps(["valhalla_digital"]),
            "assigned_jurisdictions_json": json.dumps(["CA-MB"]),
            "local_knowledge_context_json": json.dumps({
                "business_id": "valhalla_digital",
                "jurisdiction": "CA-MB",
                "data_namespace": "digital-products/ca-mb",
            }),
            "engines_json": json.dumps(["digital_products"]),
            "synchronization_status": "SYNCED",
            "isolation_state": "ISOLATED",
            "failover_state": "NOT_TRIGGERED",
            "status": "PARTIAL",
        }
        data.update(overrides)
        db = self.sessions()
        old = db.query(LegacyInstanceRegistryItem).filter_by(
            legacy_instance_id=data["legacy_instance_id"]
        ).first()
        if old:
            for key, value in data.items():
                setattr(old, key, value)
        else:
            db.add(LegacyInstanceRegistryItem(**data))
        db.commit()
        db.close()

    def submit(self, payload=None, *, headers=None):
        return self.client.post(
            "/api/business-factory/listing-drafts",
            json=payload if payload is not None else self.payload,
            headers=HEADERS if headers is None else headers,
        )

    def test_complete_internal_cycle_with_persistent_receipt(self):
        start = self.submit()
        self.assertEqual(start.status_code, 200, start.text)
        action_id = start.json()["action_id"]
        self.assertEqual(start.json()["status"], "queued")

        not_approved = self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
        self.assertEqual(not_approved.status_code, 200)
        self.assertEqual(not_approved.json()["status"], "idle")

        approved = self.client.post(
            f"/api/business-factory/actions/{action_id}/approve",
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"},
            headers=HEADERS,
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertFalse(approved.json()["external_actions_allowed"])

        executed = self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
        self.assertEqual(executed.status_code, 200, executed.text)
        result = executed.json()
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["verified"])
        self.assertEqual(result["receipt"]["external_effects"], 0)
        self.assertFalse(result["receipt"]["sales_verified"])

        db = self.sessions()
        media = db.query(MediaContent).all()
        self.assertEqual(len(media), 1)
        stored = json.loads(media[0].body)
        self.assertEqual(stored["title"], self.payload["title"])
        self.assertEqual(stored["commercial_status"], "NOT_PUBLISHED")
        self.assertIsNone(stored["purchase_url"])
        self.assertFalse(stored["delivery_configured"])
        self.assertEqual(stored["price_cents"], 1900)
        self.assertEqual(
            hashlib.sha256(media[0].body.encode("utf-8")).hexdigest(),
            result["receipt"]["sha256"],
        )
        events = db.query(LegacyOrchestrationEvent).all()
        self.assertEqual(
            {event.event_type for event in events},
            {"FACTORY_WORK_QUEUED", "FACTORY_OWNER_APPROVED", "FACTORY_ARTIFACT_VERIFIED"},
        )
        self.assertEqual(db.query(LegacyInstanceWorkItem).first().status, "completed")
        db.close()

        status = self.client.get(f"/api/business-factory/actions/{action_id}", headers=HEADERS)
        self.assertTrue(status.json()["internal_artifact_verified"])
        self.assertFalse(status.json()["externally_published"])
        self.assertFalse(status.json()["payment_verified"])

        again = self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
        self.assertEqual(again.json()["status"], "idle")
        repeated_submit = self.submit()
        self.assertTrue(repeated_submit.json()["duplicate"])
        self.assertEqual(repeated_submit.json()["action_id"], action_id)

        db = self.sessions()
        self.assertEqual(db.query(MediaContent).count(), 1)
        self.assertEqual(db.query(LegacyInstanceWorkItem).count(), 1)
        db.close()

    def test_authentication_and_approval_fail_closed(self):
        self.assertEqual(self.submit(headers={}).status_code, 401)
        self.assertEqual(self.submit(headers={"X-Business-Factory-Key": "wrong"}).status_code, 401)
        os.environ.pop("VALHALLA_FACTORY_KEY", None)
        self.assertEqual(self.submit().status_code, 503)
        os.environ["VALHALLA_FACTORY_KEY"] = HEADERS["X-Business-Factory-Key"]

        start = self.submit()
        self.assertEqual(start.status_code, 200, start.text)
        action_id = start.json()["action_id"]
        no_confirmation = self.client.post(
            f"/api/business-factory/actions/{action_id}/approve",
            json={"confirmation": "PUBLISH_EXTERNALLY"},
            headers=HEADERS,
        )
        self.assertEqual(no_confirmation.status_code, 422)
        self.assertEqual(
            self.client.post("/api/business-factory/actions/run-once", headers=HEADERS).json()["status"],
            "idle",
        )

    def test_legacy_scope_and_idempotency_enforced(self):
        bad = dict(self.payload, jurisdiction="US-FL", request_key="separate-wrong-jurisdiction")
        self.assertEqual(self.submit(bad).status_code, 409)
        bad_engine = dict(self.payload, engine_id="unapproved", request_key="other-engine-9876")
        self.assertEqual(self.submit(bad_engine).status_code, 409)
        self.seed_instance(failover_state="FAILED")
        self.assertEqual(self.submit().status_code, 409)
        self.seed_instance(failover_state="NOT_TRIGGERED")
        self.assertEqual(self.submit().status_code, 200)
        altered = dict(self.payload, price_cents_cad=2900)
        self.assertEqual(self.submit(altered).status_code, 409)

    def test_tampered_approval_and_artifact_cannot_verify(self):
        response = self.submit()
        action_id = response.json()["action_id"]
        self.client.post(
            f"/api/business-factory/actions/{action_id}/approve",
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"},
            headers=HEADERS,
        )
        db = self.sessions()
        item = db.query(LegacyInstanceWorkItem).first()
        payload = json.loads(item.payload_json)
        payload["price_cents_cad"] = 29900
        item.payload_json = json.dumps(payload)
        db.commit()
        db.close()
        blocked = self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
        self.assertEqual(blocked.json()["status"], "blocked")
        self.assertFalse(blocked.json()["verified"])

    def test_changed_artifact_invalidates_receipt(self):
        response = self.submit()
        action_id = response.json()["action_id"]
        self.client.post(
            f"/api/business-factory/actions/{action_id}/approve",
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"},
            headers=HEADERS,
        )
        self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
        db = self.sessions()
        media = db.query(MediaContent).first()
        self.assertIsNotNone(media)
        media.body = "tampered output"
        db.commit()
        db.close()
        status = self.client.get(f"/api/business-factory/actions/{action_id}", headers=HEADERS)
        self.assertEqual(status.status_code, 200)
        self.assertFalse(status.json()["internal_artifact_verified"])
        self.assertIsNone(status.json()["receipt"])


    def test_missing_schema_blocks_route_without_creating_tables(self):
        MediaContent.__table__.drop(bind=self.engine)
        result = self.submit()
        self.assertEqual(result.status_code, 503, result.text)
        self.assertEqual(result.json()["detail"]["error"], "BUSINESS_FACTORY_SCHEMA_NOT_READY")
        self.assertIn("media_contents", result.json()["detail"]["missing_tables"])

    def test_same_request_key_cannot_change_engine_or_jurisdiction(self):
        first = self.submit()
        self.assertEqual(first.status_code, 200, first.text)
        changed = dict(self.payload, engine_id="other_engine")
        self.assertEqual(self.submit(changed).status_code, 409)
        changed = dict(self.payload, jurisdiction="CA-ON")
        self.assertEqual(self.submit(changed).status_code, 409)
        changed = dict(self.payload, industry="different_industry")
        self.assertEqual(self.submit(changed).status_code, 409)


    def test_emergency_stop_prevents_approved_draft_from_executing(self):
        action = self.submit().json()["action_id"]
        approved = self.client.post(
            f"/api/business-factory/actions/{action}/approve",
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"}, headers=HEADERS,
        )
        self.assertEqual(approved.status_code, 200, approved.text)

        from unittest.mock import patch
        with patch.dict(os.environ, {"VALHALLA_EMERGENCY_STOP": "true"}):
            response = self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["status"], "blocked")
            self.assertEqual(response.json()["reason"], "EMERGENCY_STOP_ACTIVE")
            self.assertFalse(response.json()["verified"])

        db = self.sessions()
        self.assertEqual(db.query(MediaContent).count(), 0)
        self.assertEqual(db.query(LegacyInstanceWorkItem).first().status, "queued")
        db.close()

    def test_database_kill_switch_prevents_approved_draft(self):
        from app.models.go_live_state import GoLiveState

        GoLiveState.__table__.create(bind=self.engine)
        db = self.sessions()
        db.add(GoLiveState(id=1, go_live_enabled=False, kill_switch_engaged=False))
        db.commit()
        db.close()

        action = self.submit().json()["action_id"]
        approved = self.client.post(
            f"/api/business-factory/actions/{action}/approve",
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"}, headers=HEADERS,
        )
        self.assertEqual(approved.status_code, 200, approved.text)

        db = self.sessions()
        state = db.query(GoLiveState).first()
        state.kill_switch_engaged = True
        db.commit()
        db.close()

        blocked = self.client.post("/api/business-factory/actions/run-once", headers=HEADERS)
        self.assertEqual(blocked.status_code, 200, blocked.text)
        self.assertEqual(blocked.json()["status"], "blocked")
        self.assertEqual(blocked.json()["reason"], "EMERGENCY_STOP_ACTIVE")

        db = self.sessions()
        self.assertEqual(db.query(MediaContent).count(), 0)
        db.close()


    def grant(self, **overrides):
        payload = {k: self.payload[k] for k in (
            "legacy_instance_id", "business_id", "engine_id", "jurisdiction", "product_id"
        )}
        payload.update(mandate_id="draft-mandate-01", ttl_seconds=3600,
                       max_uses=2, max_price_cents_cad=2500)
        payload.update(overrides)
        response = self.client.post("/api/business-factory/mandates", json=payload, headers=HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json()["external_effects_authorized"])
        return payload

    def run_worker(self):
        response = self.client.post("/api/business-factory/actions/run-once", headers=WORKER_HEADERS)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_worker_cannot_grant_or_approve_own_authority(self):
        grant = {k: self.payload[k] for k in (
            "legacy_instance_id", "business_id", "engine_id", "jurisdiction", "product_id"
        )}
        grant.update(mandate_id="unauthorized-01", ttl_seconds=3600,
                     max_uses=2, max_price_cents_cad=2500)
        response = self.client.post("/api/business-factory/mandates", json=grant, headers=WORKER_HEADERS)
        self.assertEqual(response.status_code, 401)
        item = self.submit().json()["action_id"]
        approve = self.client.post(f"/api/business-factory/actions/{item}/approve",
            json={"confirmation": "APPROVE_INTERNAL_DRAFT"}, headers=WORKER_HEADERS)
        self.assertEqual(approve.status_code, 401)
        self.assertEqual(self.run_worker()["status"], "idle")

    def test_standing_authority_reuses_grant_but_enforces_cap(self):
        mandate = self.grant()
        for i in range(3):
            request = dict(self.payload, request_key=f"mandate-test-{i}", mandate_id=mandate["mandate_id"])
            queued = self.submit(request, headers=WORKER_HEADERS)
            self.assertEqual(queued.status_code, 200, queued.text)
        for _ in range(2):
            result = self.run_worker()
            self.assertEqual(result["status"], "completed", result)
            self.assertEqual(result["receipt"]["authority_mode"], "STANDING_MANDATE")
            self.assertEqual(result["receipt"]["external_effects"], 0)
        denied = self.run_worker()
        self.assertEqual(denied["reason"], "MANDATE_EXHAUSTED")
        with self.sessions() as db:
            self.assertEqual(db.query(MediaContent).count(), 2)

    def test_mandate_revocation_prevents_queued_work(self):
        grant = self.grant()
        self.assertEqual(self.submit(dict(self.payload, mandate_id=grant["mandate_id"]),
                                     headers=WORKER_HEADERS).status_code, 200)
        path = f"/api/business-factory/mandates/{grant['mandate_id']}/revoke"
        self.assertEqual(self.client.post(path, headers=WORKER_HEADERS).status_code, 401)
        self.assertEqual(self.client.post(path, headers=HEADERS).status_code, 200)
        self.assertEqual(self.run_worker()["reason"], "MANDATE_REVOKED")

    def test_mandate_scope_and_price_are_enforced(self):
        grant = self.grant()
        for i, change in enumerate([{"product_id": "other_product"}, {"price_cents_cad": 2900}]):
            payload = dict(self.payload, request_key=f"scope-test-{i}", mandate_id=grant["mandate_id"], **change)
            self.assertEqual(self.submit(payload, headers=WORKER_HEADERS).status_code, 200)
        self.assertEqual(self.run_worker()["reason"], "MANDATE_LIMIT_EXCEEDED")
        with self.sessions() as db:
            self.assertEqual(db.query(MediaContent).count(), 0)

    def test_mandate_expiry_is_enforced(self):
        from unittest.mock import patch
        grant = self.grant(ttl_seconds=60)
        self.assertEqual(self.submit(dict(self.payload, mandate_id=grant["mandate_id"]),
                                     headers=WORKER_HEADERS).status_code, 200)
        with patch("app.services.prime_business_execution.time.time",
                   return_value=grant["ttl_seconds"] + 9_999_999_999):
            self.assertEqual(self.run_worker()["reason"], "MANDATE_EXPIRED")


if __name__ == "__main__":
    unittest.main()
