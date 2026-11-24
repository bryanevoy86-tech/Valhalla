from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.integrations.docusign import client as docusign_client
from app.integrations.quickbooks import client as quickbooks_client
from app.integrations.stripe import payouts as stripe_payouts
from app.jobs import notification_jobs
from app.models.go_live_state import GoLiveState
from app.models.notify import Outbox
from app.services.contracts.service import ContractPipeline
from app.services.launch_readiness import capability_release_holds


def test_acquisition_release_hold_preserves_outbox_even_with_historical_live_state(monkeypatch):
    engine = create_engine("sqlite://")
    GoLiveState.__table__.create(engine)
    Outbox.__table__.create(engine)

    def unexpected(*args, **kwargs):
        raise AssertionError("Held acquisition must never construct an outbound client")

    monkeypatch.setattr(notification_jobs.httpx, "Client", unexpected)
    monkeypatch.setattr(notification_jobs.smtplib, "SMTP", unexpected)
    monkeypatch.setattr(notification_jobs, "SessionLocal", lambda: Session(engine))
    with Session(engine) as db:
        db.add_all([GoLiveState(id=1, go_live_enabled=True, kill_switch_engaged=False),
                    Outbox(kind="email", target="example@example.invalid"),
                    Outbox(kind="webhook", target="https://example.invalid")])
        db.commit()
        holds = capability_release_holds(db)
        assert len(holds["channels"]) == 8
        assert {channel["status"] for channel in holds["channels"].values()} == {"HELD"}
        reason = holds["channels"]["customer_acquisition_and_sales"]["release_blocker"]
        assert holds["external_authority"] is False
        assert notification_jobs.dispatch_pending() == {
            "ok": False, "status": "held", "reason": reason, "sent": 0, "error": 0,
        }
        assert [(row.status, row.attempts, row.sent_at) for row in db.query(Outbox).order_by(Outbox.id)] == [
            ("queued", 0, None), ("queued", 0, None),
        ]


def test_notification_email_send_guard_blocks_before_side_effect(monkeypatch):
    def fake_enforce(*_args, **_kwargs):
        raise HTTPException(status_code=409, detail="blocked")

    monkeypatch.setattr(notification_jobs, "enforce_engine", fake_enforce)

    row = Outbox(kind="email", target="owner@example.com", subject="x", payload_json="{}")

    try:
        notification_jobs._send_email(row)
        assert False, "expected shadow guard to block"
    except HTTPException as exc:
        assert exc.status_code == 409


def test_stripe_payout_calls_enforcement_guard(monkeypatch):
    captured = {}

    def fake_enforce(engine_name, action, details=None):
        captured["engine"] = engine_name
        captured["action"] = action.name
        captured["details"] = details or {}

    monkeypatch.setattr(stripe_payouts, "enforce_engine", fake_enforce)
    monkeypatch.setattr(stripe_payouts, "is_live", lambda: False)

    result = stripe_payouts.payout_to_bank(12500, "OPERATIONS")
    assert result["status"] == "sandbox"
    assert captured["engine"] == "wholesaling"
    assert captured["action"] == "MONEY_MOVE"
    assert captured["details"]["provider"] == "stripe"


def test_quickbooks_post_calls_enforcement_guard(monkeypatch):
    captured = {}

    def fake_enforce(engine_name, action, details=None):
        captured["engine"] = engine_name
        captured["action"] = action.name
        captured["details"] = details or {}

    monkeypatch.setattr(quickbooks_client, "enforce_engine", fake_enforce)
    monkeypatch.setattr(quickbooks_client, "is_live", lambda: False)

    result = quickbooks_client.post_journal_entry({"type": "profit", "account": "1000"})
    assert result["status"] == "sandbox"
    assert captured["engine"] == "wholesaling"
    assert captured["action"] == "MONEY_MOVE"
    assert captured["details"]["provider"] == "quickbooks"


def test_docusign_send_calls_enforcement_guard(monkeypatch):
    captured = {}

    def fake_enforce(engine_name, action, details=None):
        captured["engine"] = engine_name
        captured["action"] = action.name
        captured["details"] = details or {}

    monkeypatch.setattr(docusign_client, "enforce_engine", fake_enforce)
    monkeypatch.setattr(docusign_client, "is_live", lambda: False)

    result = docusign_client.send_envelope("contract-1", "sig@example.com", "https://doc")
    assert result["status"] == "sandbox"
    assert captured["engine"] == "wholesaling"
    assert captured["action"] == "CONTRACT_SEND"
    assert captured["details"]["provider"] == "docusign"


def test_contract_pipeline_send_for_signature_hits_guard_first(monkeypatch):
    class GuardRaised(Exception):
        pass

    def fake_guard(_engine_name="wholesaling"):
        raise GuardRaised("blocked")

    monkeypatch.setattr("app.services.contracts.service.guard_contract_send", fake_guard)

    svc = ContractPipeline.__new__(ContractPipeline)
    svc.db = None

    try:
        ContractPipeline.send_for_signature(svc, "contract-1", "subject", "message", "tester")
        assert False, "expected guard invocation"
    except GuardRaised:
        pass
