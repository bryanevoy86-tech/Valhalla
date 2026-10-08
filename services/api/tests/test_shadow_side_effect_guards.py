from __future__ import annotations

from fastapi import HTTPException

from app.integrations.docusign import client as docusign_client
from app.integrations.quickbooks import client as quickbooks_client
from app.integrations.stripe import payouts as stripe_payouts
from app.jobs import notification_jobs
from app.models.notify import Outbox
from app.services.contracts.service import ContractPipeline


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
