"""Real PostgreSQL integration: legacy work, owner approval and durable receipt.

Runs ONLY against a disposable CI PostgreSQL database named valhalla_factory_ci.
Never point FACTORY_TEST_POSTGRES_URL at a Render, staging or production DB.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import threading
import types
import unittest
from uuid import uuid4

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
from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.db import get_db  # noqa: E402
from app.models.completion_registry import (  # noqa: E402
    LegacyInstanceRegistryItem, LegacyInstanceWorkItem, LegacyOrchestrationEvent,
)
from app.models.prime_specialist_schedule import PrimeScheduleTrigger, PrimeSpecialistSchedule  # noqa: E402
from app.models.specialist_assignment import SpecialistAssignment, SpecialistTrigger  # noqa: E402
from app.services.specialist_triggers import enqueue_prime, enqueue_research, outcome_scope_key  # noqa: E402
from app.models.media_engine import MediaContent  # noqa: E402
from app.models.norns_forecast import NornsForecast  # noqa: E402
from app.pantheon.forecasts import sweep_scoped_outcomes  # noqa: E402
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
    SpecialistAssignment,
    SpecialistTrigger,
    PrimeSpecialistSchedule,
    PrimeScheduleTrigger,
    NornsForecast,
]


@unittest.skipUnless(url, "Disposable Postgres database is not configured")
class FactoryPostgresTests(unittest.TestCase):
    def test_simultaneous_specialist_sources_survive_a_rolled_back_claim(self):
        scope_key = outcome_scope_key({"business_id": "queue-fixture"})
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        assignment_id = uuid4()
        with self.sessions.begin() as db:
            db.add(SpecialistAssignment(id=assignment_id, role="MIMIR", scope_key=scope_key,
                                       scope={"business_id": "queue-fixture"}, next_due_at=now,
                                       expires_at=now + timedelta(hours=1), state="active", cadence_seconds=60))
        barrier = threading.Barrier(3)

        def publish(event_id):
            with self.sessions.begin() as db:
                barrier.wait(timeout=5)
                enqueue_research(db, scope_key, event_id, now)

        from concurrent.futures import ThreadPoolExecutor

        events = {"ECON-concurrent", "DISCOVERY-concurrent", "OUTCOME-concurrent"}
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(publish, events, timeout=10))
        with self.sessions() as interrupted, self.sessions() as other_worker:
            claim = select(SpecialistAssignment).where(SpecialistAssignment.id == assignment_id).with_for_update(
                key_share=True, skip_locked=True,
            )
            assert interrupted.scalar(claim) is not None
            assert other_worker.scalar(claim) is None
            interrupted.delete(interrupted.get(SpecialistTrigger, (assignment_id, "OUTCOME-concurrent")))
            interrupted.flush()
            interrupted.rollback()
        with self.sessions.begin() as db:
            enqueue_research(db, scope_key, "OUTCOME-concurrent", now)
            remaining = db.scalars(select(SpecialistTrigger.event_id).where(
                SpecialistTrigger.assignment_id == assignment_id,
            ))
            self.assertEqual(set(remaining), events)

    def test_prime_economic_wakeups_are_scoped_idempotent_and_transaction_bound(self):
        from concurrent.futures import ThreadPoolExecutor

        scope_key = outcome_scope_key({"legacy_instance_id": "target"})
        mirror_key = outcome_scope_key({"legacy_instance_id": "other"})
        target, other, mirror = uuid4(), uuid4(), uuid4()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        with self.sessions.begin() as db:
            for schedule_id, key, subscription in (
                (target, scope_key, "on_economic_reassessment"),
                (other, scope_key, "on_verified_outcome"),
                (mirror, mirror_key, "on_economic_reassessment"),
            ):
                db.add(PrimeSpecialistSchedule(
                    id=schedule_id, request={subscription: True}, cadence_seconds=300,
                    next_due_at=now, expires_at=now + timedelta(hours=1),
                    state="active", outcome_scope_key=key,
                ))

        barrier = threading.Barrier(3)

        def send(event):
            with self.sessions.begin() as db:
                barrier.wait(timeout=5)
                enqueue_prime(db, scope_key, event, now, subscription="on_economic_reassessment")

        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(send, ("ECON-one", "ECON-one", "ECON-two"), timeout=10))
        with self.sessions() as interrupted:
            enqueue_prime(interrupted, scope_key, "ECON-rollback", now, subscription="on_economic_reassessment")
            interrupted.rollback()
        with self.sessions() as db:
            actual = db.execute(select(PrimeScheduleTrigger.schedule_id, PrimeScheduleTrigger.event_id)).all()
            self.assertEqual(set(actual), {(target, "ECON-one"), (target, "ECON-two")})

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

    def test_norns_sweep_recovers_from_rolled_back_claim_and_is_scope_bound(self):
        action = self.queue_and_approve()
        scope = {key: self.payload[key] for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
        at = datetime.now(timezone.utc).replace(tzinfo=None)
        forecast_id = uuid4()
        with self.sessions.begin() as db:
            db.add(NornsForecast(id=forecast_id, action_id=action, probability_bp=4000,
                                 issued_at=at - timedelta(minutes=2), deadline_at=at - timedelta(minutes=1)))
        with self.sessions() as interrupted, self.sessions() as worker:
            self.assertEqual(sweep_scoped_outcomes(interrupted, scope, at)["resolved_ids"], [str(forecast_id)])
            self.assertEqual(sweep_scoped_outcomes(worker, scope, at)["deferred_count"], 1)
            worker.rollback()
            interrupted.rollback()
        with self.sessions.begin() as worker:
            self.assertEqual(sweep_scoped_outcomes(worker, {**scope, "jurisdiction": "CA-ON"}, at)["resolved_ids"], [])
            self.assertEqual(sweep_scoped_outcomes(worker, scope, at)["resolved_ids"], [str(forecast_id)])
        with self.sessions() as worker:
            self.assertEqual(sweep_scoped_outcomes(worker, scope, at)["resolved_ids"], [])
            label = worker.get(NornsForecast, forecast_id)
            self.assertEqual(label.observed_outcome, 0)
            self.assertEqual(label.evidence_ref, f"FACTORY_DEADLINE_NO_RECEIPT:{action}")

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


    def test_polling_tick_runs_approved_work_from_fresh_sessions(self):
        import runpy
        from app.routers.prime_business_factory import require_factory_schema
        worker = runpy.run_path(str(ROOT / "services/api/tools/cron/business_factory_worker.py"))
        action_id = self.queue_and_approve()
        result = worker["tick"](self.sessions, run_one_approved_draft, require_factory_schema)
        self.assertEqual(result, {"status": "internal_artifact_verified", "verified": True})
        self.assertEqual(worker["tick"](self.sessions, run_one_approved_draft, require_factory_schema)["status"], "idle")
        status = self.client.get(f"/api/business-factory/actions/{action_id}", headers=HEADERS)
        self.assertTrue(status.json()["internal_artifact_verified"])
        with self.sessions() as db:
            self.assertEqual(db.query(MediaContent).count(), 1)

    def test_worker_failure_after_artifact_flush_rolls_back_and_retries(self):
        from unittest.mock import patch
        from app.services import prime_business_execution as factory
        action_id = self.queue_and_approve()
        # The actual MediaContent row has been inserted but not committed when
        # the receipt writer is invoked. Inject a failure at that boundary.
        def fail_receipt(*args, **kwargs):
            self.assertEqual(kwargs["event_type"], factory.RECEIPT_EVENT)
            raise RuntimeError("injected receipt failure")

        with self.sessions() as db, patch.object(factory, "_event", side_effect=fail_receipt):
            with self.assertRaisesRegex(RuntimeError, "injected receipt failure"):
                run_one_approved_draft(db)
        with self.sessions() as db:
            self.assertEqual(db.query(MediaContent).count(), 0)
            self.assertEqual(db.query(LegacyOrchestrationEvent).filter_by(
                event_type=factory.RECEIPT_EVENT).count(), 0)
            self.assertEqual(db.query(LegacyInstanceWorkItem).filter_by(
                action_id=action_id).one().status, "queued")
        with self.sessions() as db:
            completed = run_one_approved_draft(db)
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(completed["receipt"]["action_id"], action_id)
        with self.sessions() as db:
            self.assertEqual(run_one_approved_draft(db)["status"], "idle")
            self.assertEqual(db.query(MediaContent).count(), 1)

    def test_committed_internal_effect_survives_lost_worker_acknowledgement(self):
        from unittest.mock import patch
        action_id = self.queue_and_approve()
        with self.sessions() as db:
            real_commit = db.commit
            def commit_then_lose_ack():
                real_commit()
                raise RuntimeError("injected lost commit acknowledgement")
            with patch.object(db, "commit", side_effect=commit_then_lose_ack):
                with self.assertRaisesRegex(RuntimeError, "lost commit acknowledgement"):
                    run_one_approved_draft(db)
        with self.sessions() as db:
            self.assertEqual(run_one_approved_draft(db)["status"], "idle")
            self.assertEqual(db.query(MediaContent).count(), 1)
            self.assertEqual(db.query(LegacyOrchestrationEvent).filter_by(
                event_type="FACTORY_ARTIFACT_VERIFIED").count(), 1)
        result = self.client.get(f"/api/business-factory/actions/{action_id}", headers=HEADERS)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertTrue(result.json()["internal_artifact_verified"])
        self.assertFalse(result.json()["payment_verified"])

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
            # Both requests reached the Legacy lock after their first missing-key lookup.
            barrier.wait(timeout=5)
            return original(*args, **kwargs)

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

    def test_economic_pool_serializes_competing_reservations_by_currency(self):
        from concurrent.futures import ThreadPoolExecutor
        from app.models.economic_control import EconomicPool
        from app.services.economic_control import lock_pool

        EconomicPool.__table__.create(bind=self.engine)
        try:
            with self.sessions.begin() as db:
                db.add(EconomicPool(currency="CAD"))
            start = threading.Barrier(2)

            def reserve():
                start.wait(timeout=5)
                with self.sessions.begin() as db:
                    pool = lock_pool(db, "CAD")
                    if pool.committed_minor + 120 > 170:
                        return False
                    pool.committed_minor += 120
                    return True

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = [executor.submit(reserve) for _ in range(2)]
                self.assertEqual(sorted(job.result(timeout=10) for job in results), [False, True])
            with self.sessions() as db:
                self.assertEqual(db.get(EconomicPool, "CAD").committed_minor, 120)
        finally:
            EconomicPool.__table__.drop(bind=self.engine)


    def test_conflicting_stripe_batches_leave_only_one_accounting_entry(self):
        from concurrent.futures import ThreadPoolExecutor
        from datetime import date
        from decimal import Decimal
        from unittest.mock import patch

        from sqlalchemy.exc import IntegrityError
        from app.accounting.models import Account, JournalEntry, JournalLine, Period
        from app.services.prime_business_execution import _event
        from app.services.stripe_bank_booking import _journal

        models = (Account, Period, JournalEntry, JournalLine)
        for model in models:
            model.__table__.create(bind=self.engine)
        today = date.today()
        try:
            with self.sessions.begin() as db:
                for code, type_ in (("BANK", "asset"), ("CLEARING", "asset"), ("FEES", "expense"),
                                    ("OBLIGATIONS", "liability")):
                    db.add(Account(code=code, name=code, type=type_, currency="CAD", active=True))
                db.add(Period(label="isolated", start_date=today, end_date=today, closed=False))
            start = threading.Barrier(2)
            scope = {"legacy_instance_id": "bank-race-fixture"}

            def write(batch):
                with self.sessions() as db:
                    start.wait(timeout=5)
                    try:
                        entry = _journal(db, batch, today, scope, (1920, 80, 2000))
                        _event(db, event_id="STRIPE-BANK-TX-SAME", legacy_instance_id="bank-race-fixture",
                               event_type="STRIPE_BANK_BATCH_RECONCILED", message="Synthetic contention",
                               payload={"bundle": batch})
                        db.commit()
                        return entry
                    except IntegrityError:
                        db.rollback()
                        return None

            env = {"VALHALLA_STRIPE_BOOK_" + key: key for key in ("BANK", "CLEARING", "FEES", "OBLIGATIONS")}
            with patch.dict(os.environ, env), ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(write, ("test-batch-1", "test-batch-2"), timeout=12))
            self.assertEqual(results.count(None), 1)
            with self.sessions() as db:
                self.assertEqual(db.query(JournalEntry).count(), 1)
                lines = db.scalars(select(JournalLine)).all()
                self.assertEqual(len(lines), 5)
                self.assertEqual(sum(line.debit for line in lines), Decimal("39.20"))
                self.assertEqual(sum(line.credit for line in lines), Decimal("39.20"))
        finally:
            for model in reversed(models):
                model.__table__.drop(bind=self.engine)

    def test_competing_economic_release_requests_restore_only_one_reservation(self):
        from concurrent.futures import ThreadPoolExecutor
        from datetime import date, timedelta
        from uuid import uuid4

        from fastapi import HTTPException
        from app.models.economic_control import EconomicOperation, EconomicPool, EconomicRecord
        from app.routers.economic_control import release_reservation
        from app.schemas.economic_control import Mandate, ReservationRelease
        from app.services.economic_control import load_state, operation_key, store_record

        scope = {key: self.payload[key] for key in ("legacy_instance_id", "business_id", "engine_id", "jurisdiction")}
        models = (EconomicPool, EconomicOperation, EconomicRecord)
        for model in models:
            model.__table__.create(bind=self.engine)
        key, decision = operation_key(scope), uuid4()
        try:
            with self.sessions.begin() as db:
                db.add(EconomicPool(currency="CAD", committed_minor=120))
                operation = EconomicOperation(scope_key=key, scope=scope, currency="CAD", sequence=0)
                db.add(operation)
                mandate = Mandate(id=uuid4(), scope=scope, currency="CAD", max_exposure=500,
                                  max_cumulative_loss=300, max_additional_funding=200, min_operating_reserve=50,
                                  review_by=date.today() + timedelta(days=7), minimum_period_net=0,
                                  continuation_criteria="Healthy account", suspension_criteria="Review risks",
                                  exit_criteria="Preserve assets", obligations=["Account review"])
                store_record(db, operation, "MANDATE", mandate.model_dump(mode="json"))
                store_record(db, operation, "DECISION", {"id": str(decision), "scope": scope,
                             "reserved_simulation_minor": 120, "action": "EXPAND"})
            start = threading.Barrier(2)

            def release():
                identity = uuid4()
                request = ReservationRelease(id=identity, scope=scope, decision_id=decision,
                                             reason="CANCELLED", evidence_ref=f"fixture:{identity}")
                start.wait(timeout=5)
                with self.sessions() as db:
                    try:
                        result = release_reservation(request, db)
                        return result["released_simulation_minor"]
                    except HTTPException as exc:
                        return exc.status_code

            with ThreadPoolExecutor(max_workers=2) as executor:
                jobs = [executor.submit(release) for _ in range(2)]
                self.assertEqual(sorted(job.result(timeout=10) for job in jobs), [120, 409])
            with self.sessions() as db:
                state = load_state(db, db.get(EconomicOperation, key))
                self.assertEqual(state.simulated_funding, 120)
                self.assertEqual(state.outstanding_reservations, 0)
                self.assertEqual(db.get(EconomicPool, "CAD").committed_minor, 0)
        finally:
            for model in reversed(models):
                model.__table__.drop(bind=self.engine)


if __name__ == "__main__":
    unittest.main()
