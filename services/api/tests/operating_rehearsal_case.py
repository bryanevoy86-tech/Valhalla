"""Disposable continuation of the shared independently reviewed product fixture."""
from datetime import datetime, timedelta
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
                            buyer_email, listing, scope, checksum, today, *, upstream=None):
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
    if upstream:
        source_root = f"/api/foundry/source-rehearsal/{run_id}"
        before = {**request, "source_id": upstream["export"]["source_id"], "external_key": upstream["export"]["external_key"],
                  "scenario": upstream["scenario"], "assignment_ids": upstream["assignment_ids"], "experiment_budget_minor": 100}
        before["require_scheduled_specialists"] = True
        assert client.post(source_root + "/authority", headers=owner, json=before).status_code == 503
    else:
        assert client.post(root + "/mandate", headers=owner, json=request).status_code == 503
    monkeypatch.setenv("VALHALLA_FOUNDRY_OPERATING_REHEARSAL", "1")
    monkeypatch.setenv("VALHALLA_FOUNDRY_FIXTURE_SECRET", "disposable-payment-signing-peer")
    if not upstream:
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
    authorized_worker_env["PYTHONUNBUFFERED"] = "1"

    def command(network, once=True):
        return [
            sys.executable, str(worker_file), "--port", str(network.base_url.port), "--run-id", str(run_id),
            *(["--source-to-outcome"] if upstream else []), *(["--once"] if once else []),
        ]

    def worker(network, *expected, code=0):
        result = subprocess.run(command(network), env=authorized_worker_env, capture_output=True,
                                text=True, timeout=20, check=False)
        assert result.returncode == code, (result.stdout, result.stderr)
        data = json.loads(result.stdout)
        if expected:
            assert (data["status"], data.get("phase", data.get("reason"))) == expected, data
        return data

    if upstream:
        with serve(client, app=app) as server:
            listing = source_chain(client, server, engine, monkeypatch, before, owner, upstream, worker, command,
                                   authorized_worker_env, source_root, today, owner_session, buyer_session)
        engine.dispose()

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
            owner_probe = peer.post(root + "/buyer", headers=owner_session,
                                    json={"action": "enrolled", "sha256": terms})
            assert owner_probe.status_code == 403
            if upstream:
                upstream["owner_sessions"].append(("POST", root + "/buyer", owner_probe.status_code))
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
            if upstream:
                trace = second.get(source_root)
                assert trace.status_code == 200, trace.text
                full = trace.json()
                source_rows = full["source_receipts"]
                assert full["operating_receipts"] == receipts
                assert receipts[0]["evidence"]["upstream_sha256"] == receipts[0]["previous_sha256"] == source_rows[-1]["sha256"]
                assert all(x.get("recorded_at") for x in [*source_rows, *receipts])
                types = [x["actor"] for x in source_rows if x["actor"].startswith("OWNER")]
                assert types[0] == "OWNER_INITIAL_AUTHORITY" and types[-1] == "OWNER_FINAL_MANDATE"
                assert types[1:-1] and set(types[1:-1]) == {"OWNER_MATERIAL_DISPOSITION"}
                approved = [(method, path, status) for method, path, status in upstream["owner_http"] if status < 300]
                assert approved[-1][1].endswith("/mandate")
                assert sum(path.endswith("/disposition") for _, path, _ in approved) == len(types) - 2
                assert sum(path.endswith("/mandate") for _, path, _ in approved if "/source-rehearsal/" in path) == 1
                print("FOUNDRY_SOURCE_TO_OUTCOME", json.dumps({
                    "source_transitions": [{k: r[k] for k in ("action_id", "actor", "recorded_at", "sha256", "previous_sha256")}
                                           for r in source_rows],
                    "review_receipts": [{k: r[k] for k in ("id", "reviewer_id", "artifact_sha256", "result_sha256", "disposition")}
                                        for r in full["review_briefing"]],
                    "owner_key_requests": upstream["owner_http"], "owner_key_success_count": len(approved),
                    "owner_session_requests": upstream["owner_sessions"],
                    "routine_owner_actions_after_final_mandate": 0,
                }, sort_keys=True))
            with Session(engine) as db:
                assert db.query(FoundryRehearsalOrder).count() == 1
                assert db.query(FoundryRehearsalPayment).count() == db.query(FoundryFixtureSettlement).count() == 2
                assert db.query(RevenueLedger).count() == 0
                correction = db.get(FoundryFixtureSettlement, event()["id"])
                correction.amount_minor -= 1
                db.commit()
            worker(second, "blocked", None, code=2)
            print("FOUNDRY_OPERATING_REHEARSAL", json.dumps({
                "transitions": [{key: r[key] for key in ("action_id", "phase", "actor", "recorded_at", "sha256", "previous_sha256")}
                                for r in receipts],
                "interruption_recovered": True, "failed_accounting_transaction_rolled_back": True,
                "outcome_replay_denied_after_evidence_change": True,
                "owner_routine_events_after_mandate": 0, "commercial_revenue_verified": False,
            }, sort_keys=True))


def source_chain(client, network, engine, monkeypatch, authority, owner, upstream, worker, command, env, root, today,
                 owner_session, buyer_session):
    from app.models.foundry_evidence import FoundryEvidence
    from app.pantheon.monitor import SCHEDULED_WORKER, run_scheduled_assignment, trigger_report_id
    from app.services.foundry_intake import source_signature_message

    start = client.post(root + "/authority", headers=owner, json=authority)
    assert start.status_code == 200, start.text
    worker(network, "waiting", "SIGNED_SOURCE")
    cron = Path(__file__).resolve().parents[1] / "tools" / "cron"
    reviewer = os.environ["VALHALLA_LOKI_REVIEWER_ID"]
    key = os.environ["VALHALLA_LOKI_REVIEWER_KEY"]
    publisher = httpx.Client(base_url=network.base_url, trust_env=False)
    reviewer_env = {k: v for k, v in env.items() if k != "VALHALLA_PRIME_CONTROL_KEY"}
    reviewer_env.update(VALHALLA_LOKI_ANALYST_ENABLED="1", VALHALLA_LOKI_QUEUE_URL=str(network.base_url),
                        VALHALLA_LOKI_REVIEWER_ID=reviewer, VALHALLA_LOKI_REVIEWER_KEY=key)

    def independent_review(kind):
        result = subprocess.run([sys.executable, str(cron / "loki_analyst_worker.py"), "--artifact-type", kind, "--once"],
                                env=reviewer_env, capture_output=True, text=True, timeout=20, check=False)
        assert result.returncode == 0, (result.stdout, result.stderr)
        assert json.loads(result.stdout)["status"] == "reviewed"

    def export(observed):
        document = upstream["export"]
        document = {**document, "evidence": {**document["evidence"], "evidence_id": str(uuid4()),
                                              "observed_on": observed.isoformat()}}
        document["source_signature"] = upstream["key"].sign(source_signature_message(document)).hex()
        return document

    def signed_ingress(document):
        reply = publisher.post(root + "/source", json=document)
        assert reply.status_code == 200, reply.text
        assert publisher.post(root + "/source", json=document).json() == reply.json()

    def assess(document):
        job = UUID(document["evidence"]["evidence_id"]).hex
        worker(network, "advanced", f"intake-{job}")
        # Exercise the same role entry point as the cron process in separate
        # fixture sessions. The hosted process/credential boundary is a separate gate.
        for role, assignment_id in zip(("ODIN", "NJORD"), upstream["assignment_ids"], strict=True):
            waiting = worker(network, "waiting", "SCHEDULED_SPECIALIST")
            assert waiting["role"] == role
            expected_report = trigger_report_id(assignment_id, f"DISCOVERY-{UUID(job)}")
            for _ in range(10):
                with Session(engine) as specialist_db:
                    result = run_scheduled_assignment(specialist_db, role)
                assert result["status"] == "observed", result
                if result["report_event_id"] == expected_report:
                    break
            else:
                raise AssertionError(f"{role} did not reach the exact source trigger")
            worker(network, "advanced", f"r{role.lower()}-{job}")
        source_receipts = network.get(root).json()["source_receipts"]
        assert [row["evidence"]["execution_path"] for row in source_receipts
                if row["action_id"].endswith((f"rodin-{job}", f"rnjord-{job}"))] == [SCHEDULED_WORKER] * 2
        with monkeypatch.context() as missing:
            missing.delenv("VALHALLA_LOKI_REVIEWER_KEY")
            worker(network, "blocked", None, code=2)
        worker(network, "advanced", f"review-{job}")
        worker(network, "waiting", "INDEPENDENT_LOKI")
        for kind in ("pantheon_report", "pantheon_report", "universal_opportunity"):
            independent_review(kind)
        worker(network, "advanced", f"loki-{job}")
        worker(network, "waiting", "OWNER_MATERIAL_REVIEW")
        brief = network.get(root).json()["review_briefing"]
        assert all(r["reviewer_id"] == reviewer for r in brief)
        return job, brief

    try:
        old = export(today - timedelta(days=1))
        broken = {**old, "source_signature": "0" * 128}
        assert publisher.post(root + "/source", json=broken).status_code == 409
        signed_ingress(old)
        old_job, old_brief = assess(old)
        owner_view = publisher.get(root + "/owner-briefing", headers=owner_session)
        upstream["owner_sessions"].append(("GET", root + "/owner-briefing", owner_view.status_code))
        assert owner_view.status_code == 200 and owner_view.headers["Cache-Control"] == "no-store"
        assert owner_view.json()["review_briefing"] == old_brief
        assert publisher.get(root + "/owner-briefing", headers=buyer_session).status_code == 403

        # Kill a polling process mid-wait and resume with a fresh process.
        process = subprocess.Popen(command(network, once=False), env=env, stdout=subprocess.PIPE, text=True)
        try:
            assert json.loads(process.stdout.readline())["reason"] == "OWNER_MATERIAL_REVIEW"
        finally:
            process.kill()
            process.communicate(timeout=10)
        assert process.returncode != 0

        latest = export(today)
        signed_ingress(latest)
        old_review = next(row for row in old_brief if row["kind"] == "universal_opportunity")
        denied = client.post(root + f"/reviews/{old_review['id']}/disposition", headers=owner, json={
            "artifact_sha256": old_review["artifact_sha256"], "disposition": "accept_risk", "reason": "Stale test.",
            "material_finding_ids": [x["id"] for x in old_review["findings"]],
        })
        assert denied.status_code == 409
        new_job, active = assess(latest)
        assert new_job != old_job
        assert {r["id"] for r in old_brief}.isdisjoint({r["id"] for r in active})
        for review in active:
            if review["ok_to_proceed"]:
                continue
            assert review["severity"] != "critical", review
            result = client.post(root + f"/reviews/{review['id']}/disposition", headers=owner, json={
                "artifact_sha256": review["artifact_sha256"],
                "material_finding_ids": [x["id"] for x in review["findings"] if x["tags"].get("material")],
                "disposition": "accept_risk", "reason": "Only reversible fixture work is permitted. No demand or live sale is inferred.",
            })
            assert result.status_code == 200, result.text
        worker(network, "advanced", f"decision-{new_job}")
        worker(network, "waiting", "FINAL_OWNER_MANDATE")
        decision = network.get(root).json()["source_receipts"][-1]
        aid = client.post(root + "/mandate", headers=owner, json={"decision_sha256": decision["sha256"]})
        assert aid.status_code == 200, aid.text

        # Controlled failure probes at the source-to-checkout boundary.
        from app.routers import foundry_operating_rehearsal as operating
        from app.services import economic_control

        class ExpiredClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(tz) + timedelta(hours=1)

        with monkeypatch.context() as stopped:
            stopped.setattr(operating, "datetime", ExpiredClock)
            worker(network, "blocked", None, code=2)
        with monkeypatch.context() as contained:
            contained.setattr(economic_control, "business_contained", lambda *_args, **_kwargs: True)
            worker(network, "blocked", None, code=2)
        with monkeypatch.context() as stopped:
            stopped.setenv("VALHALLA_EMERGENCY_STOP", "true")
            worker(network, "blocked", None, code=2)
        with Session(engine) as db:
            assert db.query(FoundryRehearsalOrder).count() == 0

        # A withdrawn publisher observation must hold the source-to-checkout transition.
        with Session(engine) as db:
            db.get(FoundryEvidence, UUID(latest["evidence"]["evidence_id"])).revoked = True
            db.commit()
        worker(network, "blocked", None, code=2)
        with Session(engine) as db:
            db.get(FoundryEvidence, UUID(latest["evidence"]["evidence_id"])).revoked = False
            db.commit()
        return decision["evidence"]["listing"]
    finally:
        publisher.close()
