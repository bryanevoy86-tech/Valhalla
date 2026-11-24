"""Disposable continuation of the shared independently reviewed product fixture."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import UUID, uuid4, uuid5

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.main import app
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.foundry_checkout import FoundryFixtureSettlement, FoundryRehearsalOrder, FoundryRehearsalPayment
from app.models.god_verdicts import GodVerdict
from app.models.revenue_ledger import RevenueLedger
from app.models.treasury_reconciliation import StatementAccount, StatementEntry, StatementImport
from app.routers import foundry_checkout
from app.routers.foundry_operating_rehearsal import ACTORS
from app.users.models import AccountSettings, UserProfile


def run_operating_rehearsal(client, engine, monkeypatch, serve, owner, owner_session, buyer_session,
                            buyer_email, listing, scope, checksum, today):
    for model in (FoundryFixtureSettlement, StatementAccount, StatementEntry, StatementImport, RevenueLedger):
        model.__table__.create(engine, checkfirst=True)
    with Session(engine) as db:
        buyer_id = db.scalar(select(UserProfile.user_id).where(UserProfile.email == buyer_email))
        db.scalar(select(AccountSettings).filter_by(user_id=buyer_id)).email_verified = True
        db.commit()

    run_id = uuid4()
    root = f"/api/foundry/operating-rehearsal/{run_id}"
    terms = hashlib.sha256(b"Disposable CAD offer. No sale or money. Full fixture refund on request.").hexdigest()
    request = {"listing": listing, "buyer_id": buyer_id, "campaign_id": 1, "terms_sha256": terms,
               "cost_minor": 175, "ttl_seconds": 900}
    assert client.post(root + "/mandate", headers=owner, json=request).status_code == 503
    monkeypatch.setenv("VALHALLA_FOUNDRY_OPERATING_REHEARSAL", "1")
    monkeypatch.setenv("VALHALLA_FOUNDRY_FIXTURE_SECRET", "disposable-payment-signing-peer")
    assert client.post(root + "/mandate", json=request).status_code == 401
    with monkeypatch.context() as hosted:
        hosted.setenv("APP_ENV", "staging")
        assert client.post(root + "/mandate", headers=owner, json=request).status_code == 503
    created = client.post(root + "/mandate", headers=owner, json=request)
    assert created.status_code == 200, created.text
    worker_file = Path(__file__).resolve().parents[1] / "tools" / "cron" / "foundry_operating_worker.py"
    authorized_worker_env = {key: os.environ[key] for key in (
        "PATH", "ENV", "APP_ENV", "VALHALLA_FOUNDRY_OPERATING_REHEARSAL", "VALHALLA_PRIME_CONTROL_KEY",
    ) if key in os.environ}
    authorized_worker_env["DATABASE_URL"] = "sqlite://"
    authorized_worker_env["VALHALLA_JWT_SECRET"] = "fixture-worker-import-only"
    authorized_worker_env["PYTHON_DOTENV_DISABLED"] = "1"

    def worker(network, *expected, code=0):
        result = subprocess.run(
            [sys.executable, str(worker_file), "--port", str(network.base_url.port), "--run-id", str(run_id), "--once"],
            env=authorized_worker_env, capture_output=True, text=True, timeout=20, check=False,
        )
        assert result.returncode == code, (result.stdout, result.stderr)
        data = json.loads(result.stdout)
        assert (data["status"], data.get("phase", data.get("reason"))) == expected, data
        return data

    def signed(http, suffix, doc, key, header):
        raw = json.dumps(doc, sort_keys=True).encode()
        at = str(int(time.time()))
        digest = hmac.new(key.encode(), at.encode() + b"." + raw, hashlib.sha256).hexdigest()
        return http.post(root + suffix, content=raw, headers={header: f"t={at},v1={digest}"})

    def buyer(http, action, sha):
        return http.post(root + "/buyer", json={"action": action, "sha256": sha}, headers=buyer_session)

    price = listing["price_cents_cad"]
    reference = f"pi_fixture_{run_id.hex}"

    def event(refund=False):
        return {"type": "charge.refunded" if refund else "payment_intent.succeeded", "livemode": False,
                "id": f"evt_fixture_{run_id.hex}_{'refund' if refund else 'capture'}",
                "data": {"object": {"currency": "cad", **(
                    {"payment_intent": reference, "amount_refunded": price} if refund
                    else {"id": reference, "amount_received": price}
                )}}}

    with serve(client, app=app) as first:
        with httpx.Client(base_url=first.base_url, trust_env=False) as peer:
            assert peer.post(root + "/advance").status_code == 401
            assert buyer(peer, "enrolled", terms).status_code == 409
            # Alter the stored proposal reference in the negative-test harness.
            with Session(engine) as db:
                row = db.get(GodVerdict, UUID(listing["prime_verdict_id"]))
                from copy import deepcopy

                original = deepcopy(row.metadata_json)
                modified = deepcopy(original)
                modified["owner_approval_envelope"]["independent_loki"]["result_sha256"] = "0" * 64
                row.metadata_json = modified
                db.commit()
            worker(first, "blocked", None, code=2)
            with Session(engine) as db:
                db.get(GodVerdict, UUID(listing["prime_verdict_id"])).metadata_json = original
                db.commit()
            worker(first, "advanced", "listing")
            assert peer.post(root + "/buyer", headers=owner_session,
                             json={"action": "enrolled", "sha256": terms}).status_code == 403
            assert buyer(peer, "enrolled", terms).status_code == 200
            assert buyer(peer, "purchase", "0" * 64).status_code == 409
            accepted = buyer(peer, "purchase", terms)
            assert accepted.status_code == 200, accepted.text
            assert buyer(peer, "purchase", terms).json() == accepted.json()
            worker(first, "advanced", "order")
            worker(first, "waiting", "capture")
            pay = lambda refund=False: signed(peer, "/payment", event(refund), "disposable-payment-signing-peer",
                                               "Stripe-Signature")
            assert pay(True).status_code == 409
            captured = pay()
            assert captured.status_code == 200, captured.text
            assert pay().json() == captured.json()
            monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
            worker(first, "blocked", None, code=2)
            assert peer.get(root + "/delivery", headers=buyer_session).status_code == 503
    # Close the HTTP server, worker process and database connections. Resume on a new server/port.
    engine.dispose()
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    with serve(client, app=app) as second:
        with httpx.Client(base_url=second.base_url, trust_env=False) as peer:
            worker(second, "advanced", "delivery")
            download = peer.get(root + "/delivery", headers=buyer_session)
            assert download.status_code == 200 and hashlib.sha256(download.content).hexdigest() == checksum
            ack = buyer(peer, "acknowledge", checksum)
            assert ack.status_code == 200, ack.text
            assert buyer(peer, "support", ack.json()["sha256"]).status_code == 200
            worker(second, "advanced", "refund_requested")
            worker(second, "waiting", "refund")
            refunded = signed(peer, "/payment", event(True), "disposable-payment-signing-peer", "Stripe-Signature")
            assert refunded.status_code == 200, refunded.text
            assert peer.get(root + "/delivery", headers=buyer_session).status_code == 404
            worker(second, "waiting", "statement")
            day = today.isoformat()
            doc = {"id": str(uuid5(run_id, "statement")), "scope": scope,
                   "source_id": "fixture:operating-bank", "account_ref": f"fixture:{run_id.hex}",
                   "purpose": "BUSINESS", "currency": "CAD", "start": day, "end": day, "opening_minor": 0,
                   "closing_minor": 0, "outstanding_liabilities_minor": 0, "expense_budget_minor": 0,
                   "basis": "LOCAL_STATEMENT_FIXTURE",
                   "entries": [{"external_ref": event(refund)["id"], "posted_on": day, "category": "TRANSFER",
                                "amount_minor": -price if refund else price} for refund in (False, True)]}
            bank_headers = ("disposable-bank-signing-peer", "Fixture-Bank-Signature")
            assert signed(peer, "/statement", doc, *bank_headers).status_code == 503
            monkeypatch.setenv("VALHALLA_OPERATING_FIXTURE_BANK_SECRET", bank_headers[0])
            assert signed(peer, "/statement", doc, "disposable-payment-signing-peer", bank_headers[1]).status_code == 400
            statement = signed(peer, "/statement", doc, *bank_headers)
            assert statement.status_code == 200, statement.text
            # Fail after both native settlement matches flush, before the outcome can commit.
            from fastapi import HTTPException

            def interrupt(*args, **kwargs):
                raise HTTPException(503, "Interrupted disposable accounting pass")

            with monkeypatch.context() as interrupted:
                interrupted.setattr(foundry_checkout, "_record_cost", interrupt)
                worker(second, "blocked", None, code=2)
            with Session(engine) as db:
                assert db.query(FoundryFixtureSettlement).count() == 0
            outcome = worker(second, "advanced", "outcome")
            replay = worker(second, "completed", "outcome")
            assert replay["receipt_sha256"] == outcome["receipt_sha256"]
            trace = second.get(root).json()
            receipts = trace["receipts"]
            assert [r["phase"] for r in receipts] == list(ACTORS)
            assert [r["actor"] for r in receipts].count("OWNER_AUTHORITY") == 1
            assert all(r["external_effects"] == 0 for r in receipts)
            evidence = receipts[-1]["evidence"]
            assert evidence["commercial_revenue_verified"] is False
            assert evidence["uncommitted_cash_minor"] == evidence["outstanding_obligation_minor"] == 0
            assert evidence["mimir_claim"]["period_net_minor"] == -175
            assert evidence["mimir_claim"]["verified_real_world_outcome"] is False
            with Session(engine) as db:
                assert db.query(FoundryRehearsalOrder).count() == 1
                assert db.query(FoundryRehearsalPayment).count() == db.query(FoundryFixtureSettlement).count() == 2
                assert db.query(RevenueLedger).count() == 0
                correction = db.get(FoundryFixtureSettlement, event()["id"])
                correction.amount_minor -= 1
                db.commit()
            worker(second, "blocked", None, code=2)
            print("FOUNDRY_OPERATING_REHEARSAL", json.dumps({
                "transitions": [{key: r[key] for key in ("phase", "actor", "sha256", "previous_sha256")}
                                for r in receipts],
                "interruption_recovered": True, "failed_accounting_transaction_rolled_back": True,
                "outcome_replay_denied_after_evidence_change": True,
                "owner_routine_events_after_mandate": 0, "commercial_revenue_verified": False,
            }, sort_keys=True))
