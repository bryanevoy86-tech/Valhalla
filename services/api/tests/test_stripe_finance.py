"""Signed delivery through registered ingress and independently sourced HTTP readback."""
import hashlib
import hmac
import json
import time

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import db as database
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent
from app.services.stripe_finance import read_processor_balance


def test_registered_stripe_finance_replays_and_reconciles_only_matching_capture(deal_client, monkeypatch):
    client, engine = deal_client
    StripeFinancialEvent.__table__.create(engine)
    StripeBalanceEvidence.__table__.create(engine)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr("app.webhooks.stripe.is_live", lambda: False)
    monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "fixture-owner-readback")
    secret = "synthetic-stripe-signature-key"
    monkeypatch.setenv("VALHALLA_STRIPE_EVENT_MODE", "test")
    monkeypatch.setenv("VALHALLA_STRIPE_TEST_WEBHOOK_SECRET", secret)
    monkeypatch.delenv("VALHALLA_STRIPE_READBACK_ENABLED", raising=False)

    event = {"id": "evt_CaptureA", "type": "payment_intent.succeeded", "livemode": False, "data": {"object": {
        "id": "pi_CaptureA", "object": "payment_intent", "status": "succeeded", "latest_charge": "ch_CaptureA",
        "amount_received": 1000, "currency": "cad", "metadata": {"private": "do not retain this"},
    }}}

    def deliver(payload, *, key=secret):
        raw = json.dumps(payload).encode()
        stamp = str(int(time.time()))
        digest = hmac.new(key.encode(), stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        return client.post("/webhooks/stripe", content=raw, headers={"Stripe-Signature": f"t={stamp},v1={digest}"})

    assert deliver(event, key="wrong").status_code == 400
    assert deliver({**event, "livemode": True}).status_code == 422
    first = deliver(event)
    assert first.status_code == 200, first.text
    assert first.json() == {"event_id": "evt_CaptureA", "status": "journaled", "duplicate": False,
                            "basis": "SIGNED_STRIPE_TEST", "verified_financial_effect": False}
    assert deliver(event).json()["duplicate"] is True
    changed = {**event, "data": {"object": {**event["data"]["object"], "amount_received": 1001}}}
    assert deliver(changed).status_code == 409
    assert deliver({**event, "account": "acct_External"}).status_code == 422
    assert deliver({**event, "id": "evt_CaptureReplay"}).status_code == 200
    url = "/api/governance/floor/stripe-events/evt_CaptureA/processor-readback"
    assert client.post(url).status_code == 401
    assert client.post(url, headers={"X-Owner-Mandate-Key": "fixture-owner-readback"}).status_code == 503

    charge = {"id": "ch_CaptureA", "object": "charge", "payment_intent": "pi_CaptureA", "livemode": False,
              "currency": "cad", "amount_captured": 1000, "status": "succeeded", "paid": True,
              "captured": True, "disputed": False, "refunded": False, "amount_refunded": 0,
              "balance_transaction": "txn_CaptureA"}
    balance = {"id": "txn_CaptureA", "object": "balance_transaction", "source": charge["id"], "type": "charge",
               "currency": "cad", "amount": 1000, "fee": 40, "net": 960,
               "available_on": int(time.time()) - 5, "status": "pending"}

    def upstream(request):
        assert request.method == "GET"
        responses = {"/v1/account": {"id": "acct_ValhallaTest", "object": "account"},
                     "/v1/charges/ch_CaptureA": charge, "/v1/balance_transactions/txn_CaptureA": balance}
        return httpx.Response(200, json=responses[request.url.path])

    with Session(engine) as db, httpx.Client(base_url="https://example.invalid",
                                             transport=httpx.MockTransport(upstream)) as adapter:
        assert db.get(StripeFinancialEvent, "evt_CaptureA").snapshot.get("metadata") is None

        def read(event_id="evt_CaptureA", account="acct_ValhallaTest"):
            return read_processor_balance(db, event_id, client=adapter, account_id=account, live=False)

        with pytest.raises(HTTPException, match="identity mismatch"):
            read(account="acct_Wrong")
        with pytest.raises(HTTPException, match="pending"):
            read()
        assert db.query(StripeBalanceEvidence).count() == 0
        balance["status"] = "available"
        receipt = read()
        assert read() == receipt and receipt["net_minor"] == 960
        assert receipt["basis"] == "STRIPE_TEST_PROCESSOR_BALANCE"
        assert not receipt["bank_settlement_verified"] and not receipt["ledger_posting_created"]
        assert not receipt["entitlement_granted"]
        with pytest.raises(HTTPException, match="already has a receipt"):
            read("evt_CaptureReplay")
        assert db.query(StripeBalanceEvidence).count() == 1
        charge["amount_refunded"] = 50
        with pytest.raises(HTTPException, match="refunded"):
            read()
