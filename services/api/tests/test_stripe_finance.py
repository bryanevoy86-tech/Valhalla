"""Signed delivery through registered ingress and independently sourced HTTP readback."""
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import db as database
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding
from app.services.stripe_finance import read_processor_balance
from app.services.stripe_payout_evidence import record_payout_evidence


def test_registered_stripe_finance_replays_and_reconciles_only_matching_capture(deal_client, monkeypatch):
    client, engine = deal_client
    StripeFinancialEvent.__table__.create(engine)
    StripeBalanceEvidence.__table__.create(engine)
    StripeOrderBinding.__table__.create(engine)
    LegacyOrchestrationEvent.__table__.create(engine, checkfirst=True)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr("app.webhooks.stripe.is_live", lambda: False)
    monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "fixture-owner-readback")
    secret = "synthetic-stripe-signature-key"
    monkeypatch.setenv("VALHALLA_STRIPE_EVENT_MODE", "test")
    monkeypatch.setenv("VALHALLA_STRIPE_TEST_WEBHOOK_SECRET", secret)
    monkeypatch.delenv("VALHALLA_STRIPE_READBACK_ENABLED", raising=False)
    monkeypatch.setenv("VALHALLA_STRIPE_ACCOUNT_ID", "acct_ValhallaTest")
    order_id = str(uuid4())
    scope = {"legacy_instance_id": "stripe-test-legacy", "business_id": "stripe-test-business",
             "engine_id": "stripe-test-engine", "jurisdiction": "CA-MB"}
    asset = SimpleNamespace(id=uuid4(), product_id="sample-product", sha256="b" * 64)
    monkeypatch.setattr("app.routers.foundry_checkout._listing", lambda *args: ({"sha256": "a" * 64}, asset, 1000, scope))
    binding_url = "/api/governance/floor/stripe-orders"
    keys = {"X-Owner-Mandate-Key": "fixture-owner-readback"}
    binding = {"order_id": order_id, "scope": scope, "action_id": "bfd_" + "1" * 32,
               "payment_intent_id": "pi_CaptureA"}
    assert client.post(binding_url, json=binding).status_code == 401
    assert client.post(binding_url, headers=keys, json=binding).status_code == 201
    assert client.post(binding_url, headers=keys, json={**binding, "order_id": str(uuid4())}).status_code == 409
    review_url = f"{binding_url}/{order_id}"
    assert client.get(f"/api/weweb/owner-stripe-orders/{order_id}", headers=keys).status_code == 401
    assert client.get(review_url, headers=keys).json()["status"] == "AWAITING_PROCESSOR_EVIDENCE"

    event = {"id": "evt_CaptureA", "type": "payment_intent.succeeded", "livemode": False, "data": {"object": {
        "id": "pi_CaptureA", "object": "payment_intent", "status": "succeeded", "latest_charge": "ch_CaptureA",
        "amount_received": 1000, "currency": "cad",
        "metadata": {"private": "do not retain this", "valhalla_order_id": order_id},
    }}}

    def deliver(payload, *, key=secret):
        raw = json.dumps(payload).encode()
        stamp = str(int(time.time()))
        digest = hmac.new(key.encode(), stamp.encode() + b"." + raw, hashlib.sha256).hexdigest()
        return client.post("/webhooks/stripe", content=raw, headers={"Stripe-Signature": f"t={stamp},v1={digest}"})

    monkeypatch.delenv("VALHALLA_STRIPE_EVENT_MODE")
    assert deliver(event).status_code == 503
    monkeypatch.setenv("VALHALLA_STRIPE_EVENT_MODE", "test")
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
              "balance_transaction": "txn_CaptureA", "metadata": {"valhalla_order_id": order_id}}
    balance = {"id": "txn_CaptureA", "object": "balance_transaction", "source": charge["id"], "type": "charge",
               "currency": "cad", "amount": 1000, "fee": 40, "net": 960,
               "available_on": int(time.time()) - 5, "status": "pending"}

    payout = {"id": "po_ValhallaTest", "object": "payout", "livemode": False, "automatic": True,
              "method": "standard", "type": "bank_account", "destination": "ba_ApprovedTest",
              "status": "paid", "reconciliation_status": "completed", "currency": "cad", "amount": 2100,
              "arrival_date": int(time.time())}
    listed = {"object": "list", "has_more": False, "data": []}

    def upstream(request):
        assert request.method == "GET"
        if request.url.path == "/v1/balance_transactions":
            assert request.url.params["payout"] == "po_ValhallaTest"
            assert request.url.params["source"] == "ch_CaptureA"
            return httpx.Response(200, json=listed)
        responses = {"/v1/payouts/po_ValhallaTest": payout, "/v1/account": {"id": "acct_ValhallaTest", "object": "account"},
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
        matched = client.get(review_url, headers=keys)
        assert matched.status_code == 200, matched.text
        assert matched.json()["status"] == "MATCHED_PROCESSOR_EVIDENCE"
        assert matched.json()["available_cash_minor"] is None

        def read_payout(destination="ba_ApprovedTest"):
            from uuid import UUID
            return record_payout_evidence(db, UUID(order_id), "po_ValhallaTest", client=adapter,
                                          account_id="acct_ValhallaTest", destination_id=destination, live=False)

        with pytest.raises(HTTPException, match="configured destination"):
            read_payout("ba_Wrong")
        with pytest.raises(HTTPException, match="missing or ambiguous"):
            read_payout()
        listed["data"] = [{**balance, "net": 900}]
        with pytest.raises(HTTPException, match="differs"):
            read_payout()
        listed["data"] = [balance]
        payout_receipt = read_payout()
        assert read_payout() == payout_receipt
        assert payout_receipt["capture_net_minor"] == 960
        assert payout_receipt["processor_reported_payout_minor"] == 2100
        assert payout_receipt["confirmed_bank_amount_minor"] is None and not payout_receipt["bank_settlement_verified"]
        payout["reversed_by"] = "po_Reversal"
        with pytest.raises(HTTPException, match="reversed"):
            read_payout()

        wrong_order = str(uuid4())
        assert deliver({"id": "evt_CaptureWrongOrder", **{k: v for k, v in event.items() if k not in {"id", "data"}},
                        "data": {"object": {**event["data"]["object"],
                                             "metadata": {"valhalla_order_id": wrong_order}}}}).status_code == 200
        with pytest.raises(HTTPException, match="merchant order differs"):
            read("evt_CaptureWrongOrder")
        refund = {"id": "evt_RefundA", "type": "charge.refunded", "livemode": False, "data": {"object": {
            "id": "ch_CaptureA", "object": "charge", "payment_intent": "pi_CaptureA", "currency": "cad",
            "amount_refunded": 50,
        }}}
        assert deliver(refund).status_code == 200
        assert client.get(review_url, headers=keys).json()["status"] == "REFUND_REVIEW_REQUIRED"
        second = {**binding, "order_id": str(uuid4()), "payment_intent_id": "pi_RefundFirst"}
        assert client.post(binding_url, headers=keys, json=second).status_code == 201
        refund_first = {**refund, "id": "evt_RefundFirst", "data": {"object": {
            **refund["data"]["object"], "id": "ch_RefundFirst", "payment_intent": "pi_RefundFirst",
        }}}
        assert deliver(refund_first).status_code == 200
        hold = client.get(f"{binding_url}/{second['order_id']}", headers=keys).json()
        assert hold["status"] == "REFUND_REVIEW_REQUIRED" and hold["processor_evidence"] is None
        with pytest.raises(HTTPException, match="already has a receipt"):
            read("evt_CaptureReplay")
        assert db.query(StripeBalanceEvidence).count() == 1
        charge["amount_refunded"] = 50
        with pytest.raises(HTTPException, match="refunded"):
            read()
