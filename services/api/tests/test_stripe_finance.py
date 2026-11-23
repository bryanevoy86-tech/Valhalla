"""Signed delivery through registered ingress and independently sourced HTTP readback."""
from contextlib import contextmanager
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from uuid import UUID, uuid4
from datetime import date, timedelta

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.accounting.models import Account, JournalEntry, JournalLine, Period
from app.banking.plaid_transactions import posted_credit
from app.core import db as database
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.auth_revocations import RevokedAccessToken
from app.routers.auth_weweb import _auth_runtime, _issue_access_token
from app.services.stripe_fulfillment import delivery_buyer_reference
from app.users.models import AccountSettings, UserProfile
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding
from app.services.stripe_finance import read_processor_balance
from app.services.stripe_bank_booking import BankBatchIn, _journal, bank_batch_summary, reconcile_bank_batch, scoped_bank_blockers
from app.services.stripe_payout_evidence import record_payout_evidence


@pytest.mark.parametrize("partial_refunds", [False, True, None, "reversal"],
                         ids=["payout-and-delivery", "ordered-partial-refunds", "terminal-chargeback", "bank-reversal"])
def test_registered_stripe_finance_replays_and_reconciles_only_matching_capture(deal_client, monkeypatch, partial_refunds):
    client, engine = deal_client
    StripeFinancialEvent.__table__.create(engine)
    StripeBalanceEvidence.__table__.create(engine)
    StripeOrderBinding.__table__.create(engine)
    for model in (LegacyOrchestrationEvent, Account, Period, JournalEntry, JournalLine,
                  UserProfile, AccountSettings, RevokedAccessToken):
        model.__table__.create(engine, checkfirst=True)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr("app.webhooks.stripe.is_live", lambda: False)
    monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "fixture-owner-readback")
    secret = "synthetic-stripe-signature-key"
    monkeypatch.setenv("VALHALLA_STRIPE_EVENT_MODE", "test")
    monkeypatch.setenv("VALHALLA_STRIPE_TEST_WEBHOOK_SECRET", secret)
    monkeypatch.delenv("VALHALLA_STRIPE_READBACK_ENABLED", raising=False)
    monkeypatch.setenv("VALHALLA_STRIPE_ACCOUNT_ID", "acct_ValhallaTest")
    order_id, tenant_id = str(uuid4()), str(uuid4())
    with Session(engine) as db:
        buyer = UserProfile(first_name="Fixture", last_name="Buyer", email="stripe-buyer@example.invalid")
        outsider = UserProfile(first_name="Fixture", last_name="Outsider", email="stripe-outsider@example.invalid")
        db.add_all([buyer, outsider])
        db.flush()
        subscriber_id = buyer.user_id
        for profile in (buyer, outsider):
            db.add(AccountSettings(user_id=profile.user_id, account_locked=False, password_hash="unused-fixture"))
        buyer_headers = {"Authorization": f"Bearer {_issue_access_token(_auth_runtime(), buyer)}"}
        outsider_headers = {"Authorization": f"Bearer {_issue_access_token(_auth_runtime(), outsider)}"}
        db.commit()
    buyer_metadata = {
        "valhalla_order_id": order_id, "valhalla_tenant_id": tenant_id,
        "valhalla_buyer_ref": delivery_buyer_reference(order_id, tenant_id, subscriber_id),
    }

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
        "customer": "cus_PaidBuyer", "metadata": {"private": "do not retain this", **buyer_metadata},
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
              "balance_transaction": "txn_CaptureA", "customer": "cus_PaidBuyer", "metadata": buyer_metadata}
    balance = {"id": "txn_CaptureA", "object": "balance_transaction", "source": charge["id"], "type": "charge",
               "currency": "cad", "amount": 1000, "fee": 40, "net": 960,
               "available_on": int(time.time()) - 5, "status": "pending"}

    other_id = str(uuid4())
    assert client.post(binding_url, headers=keys, json={**binding, "order_id": other_id,
                       "payment_intent_id": "pi_CaptureB"}).status_code == 201
    event_b = {**event, "id": "evt_CaptureB", "data": {"object": {**event["data"]["object"], "id": "pi_CaptureB",
        "latest_charge": "ch_CaptureB", "metadata": {"valhalla_order_id": other_id}}}}
    assert deliver(event_b).status_code == 200
    charge_b = {**charge, "id": "ch_CaptureB", "payment_intent": "pi_CaptureB",
                "balance_transaction": "txn_CaptureB", "metadata": {"valhalla_order_id": other_id}}
    balance_b = {**balance, "id": "txn_CaptureB", "source": "ch_CaptureB", "status": "available"}
    payout = {"id": "po_ValhallaTest", "object": "payout", "livemode": False, "automatic": True,
              "method": "standard", "type": "bank_account", "destination": "ba_ApprovedTest",
              "status": "paid", "reconciliation_status": "completed", "currency": "cad", "amount": 1920,
              "trace_id": {"value": "BANKREF-88397", "status": "supported"},
              "arrival_date": int(time.time())}
    listed = {"object": "list", "has_more": False, "data": []}

    native_refund = {"id": "re_FullB", "object": "refund", "payment_intent": "pi_CaptureB", "charge": "ch_CaptureB",
                     "status": "succeeded", "currency": "cad", "amount": 1000, "balance_transaction": "txn_RefundB"}
    refund_balance = {"id": "txn_RefundB", "object": "balance_transaction", "source": "re_FullB",
                      "type": "refund", "currency": "cad", "status": "available", "amount": -1000, "net": -1000,
                      "fee": 0, "available_on": int(time.time()) - 5}

    adjustments = {}
    for suffix, amount in (("PartialA", 250), ("RemainderA", 750)):
        refund_id, txn_id = f"re_{suffix}", f"txn_{suffix}"
        adjustments[f"/v1/refunds/{refund_id}"] = {
            **native_refund, "id": refund_id, "charge": charge["id"], "payment_intent": charge["payment_intent"],
            "amount": amount, "balance_transaction": txn_id,
        }
        adjustments[f"/v1/balance_transactions/{txn_id}"] = {
            **refund_balance, "id": txn_id, "source": refund_id, "amount": -amount, "net": -amount,
        }

    reversing_payout = {"id": "po_ReverseA", "object": "payout", "livemode": False,
                        "destination": "ba_ApprovedTest", "type": "bank_account", "currency": "cad",
                        "amount": -1920, "original_payout": "po_ValhallaTest", "status": "paid",
                        "arrival_date": payout["arrival_date"], "balance_transaction": "txn_ReverseA",
                        "trace_id": {"value": "BANK-DEBIT-TEST"}}
    reversal_tx = {"id": "txn_ReverseA", "object": "balance_transaction", "source": "po_ReverseA",
                   "currency": "cad", "type": "payout", "status": "available", "amount": 1920, "net": 1920, "fee": 0}
    dispute = {"id": "du_LostA", "object": "dispute", "livemode": False, "charge": "ch_CaptureA",
               "payment_intent": "pi_CaptureA", "currency": "cad", "amount": 1000, "status": "lost",
               "balance_transactions": [{"id": "txn_DisputeA"}]}
    dispute_tx = {**refund_balance, "id": "txn_DisputeA", "source": "du_LostA", "type": "adjustment",
                  "reporting_category": "dispute", "fee": 150, "net": -1150}

    def upstream(request):
        assert request.method == "GET"
        if request.url.path == "/v1/balance_transactions":
            assert request.url.params["payout"] == "po_ValhallaTest"
            source = request.url.params.get("source")
            if source == "ch_CaptureA":
                return httpx.Response(200, json=listed)
            if source == "ch_CaptureB":
                return httpx.Response(200, json={**listed, "data": [balance_b]})
            return httpx.Response(200, json={**listed, "data": [balance, balance_b]})
        responses = {"/v1/payouts/po_ValhallaTest": payout, "/v1/account": {"id": "acct_ValhallaTest", "object": "account"},
                     "/v1/charges/ch_CaptureA": charge, "/v1/balance_transactions/txn_CaptureA": balance,
                     "/v1/charges/ch_CaptureB": charge_b, "/v1/balance_transactions/txn_CaptureB": balance_b}
        responses.update({"/v1/payouts/po_ReverseA": reversing_payout,
                          "/v1/balance_transactions/txn_ReverseA": reversal_tx})
        responses.update({"/v1/disputes/du_LostA": dispute, "/v1/balance_transactions/txn_DisputeA": dispute_tx})
        responses.update({"/v1/refunds/re_FullB": native_refund, "/v1/balance_transactions/txn_RefundB": refund_balance})
        return httpx.Response(200, json=(responses | adjustments)[request.url.path])

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

        @contextmanager
        def read_only_fixture(*, live):
            assert not live
            yield adapter, "acct_ValhallaTest"

        monkeypatch.setattr("app.services.stripe_fulfillment.stripe_readback_client", read_only_fixture)
        purchase = f"/api/weweb/paid-products/{tenant_id}/{order_id}"
        gate = f"{review_url}/delivery"
        authority = {"tenant_id": tenant_id, "subscriber_id": subscriber_id, "stripe_customer_id": "cus_PaidBuyer",
                     "signed_event_id": event["id"], "commercial_rights_reference": "fixture-commercial-license",
                     "attestation": "OWNER_AUTHORIZES_EXACT_PAID_PRODUCT_DELIVERY"}
        assert client.post(gate, json=authority).status_code == 401
        assert client.post(gate, headers=keys, json={**authority, "tenant_id": str(uuid4())}).status_code == 409
        assert client.get(purchase, headers=buyer_headers).status_code == 404
        grant = client.post(gate, headers=keys, json=authority)
        assert grant.status_code == 200, grant.text
        assert client.post(gate, headers=keys, json=authority).json() == grant.json()
        assert db.query(StripeBalanceEvidence).count() == 0
        assert client.get(purchase, headers=outsider_headers).status_code == 404
        assert client.get(purchase.replace(tenant_id, str(uuid4())), headers=buyer_headers).status_code == 404
        entitlement = client.get(purchase, headers=buyer_headers)
        assert entitlement.status_code == 200 and entitlement.json()["download_enabled"] is False
        assert entitlement.headers["cache-control"] == "no-store"
        payload = {"grant_sha256": grant.json()["grant_sha256"]}
        assert client.post(purchase + "/acknowledge", headers=buyer_headers,
                           json={"grant_sha256": "0" * 64}).status_code == 409
        accepted = client.post(purchase + "/acknowledge", headers=buyer_headers, json=payload)
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["recognized_revenue_minor"] is None
        assert client.post(purchase + "/acknowledge", headers=buyer_headers, json=payload).json() == accepted.json()
        release_url = gate + "/release-liability"
        release_request = {"acknowledgment_sha256": accepted.json()["sha256"]}
        assert client.post(release_url, headers=keys, json=release_request).status_code == 409


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
        assert payout_receipt["processor_reported_payout_minor"] == 1920
        assert payout_receipt["confirmed_bank_amount_minor"] is None and not payout_receipt["bank_settlement_verified"]
        read("evt_CaptureB")
        record_payout_evidence(db, UUID(other_id), "po_ValhallaTest", client=adapter,
                               account_id="acct_ValhallaTest", destination_id="ba_ApprovedTest", live=False)
        posting_date = date.fromtimestamp(payout["arrival_date"])
        bank_item = {"account_id": "bank_test", "transaction_id": "test_tx_exact", "pending": False,
                     "amount": -19.20, "iso_currency_code": "CAD", "date": posting_date.isoformat(),
                     "payment_meta": {"reference_number": "BANKREF-88397"}}

        def bank_upstream(request):
            assert request.url.path == "/transactions/get" and request.method == "POST"
            assert json.loads(request.content)["options"]["account_ids"] == ["bank_test"]
            return httpx.Response(200, json={"transactions": [bank_item], "total_transactions": 1})

        def verify_bank(**args):
            with httpx.Client(base_url="https://bank.example.invalid",
                              transport=httpx.MockTransport(bank_upstream)) as bank_client:
                return posted_credit(bank_client, token="isolated", account_id="bank_test", trace=args["trace"],
                                     arrival=args["arrival"], amount_minor=args["amount_minor"],
                                     today=args["arrival"] + timedelta(days=1))

        def reconcile(orders):
            return reconcile_bank_batch(db, BankBatchIn(payout_id="po_ValhallaTest", order_ids=orders),
                                        client=adapter, account_id="acct_ValhallaTest", destination="ba_ApprovedTest",
                                        live=False, bank_credit=verify_bank)

        with pytest.raises(HTTPException, match="full payout"):
            reconcile([order_id])
        bank_item["pending"] = True
        with pytest.raises(HTTPException, match="pending"):
            reconcile([order_id, other_id])
        bank_item["pending"] = False
        batch = reconcile([order_id, other_id])
        assert reconcile([other_id, order_id]) == batch
        assert batch["value"]["payout_minor"] == 1920 and batch["value"]["processor_fee_minor"] == 80
        assert batch["value"]["gross_customer_obligation_minor"] == 2000
        assert batch["value"]["available_cash_minor"] is None and batch["ledger_entry_id"] is None
        assert batch["value"]["basis"] == "SYNTHETIC_BANK_REHEARSAL"
        assert db.query(JournalEntry).count() == 0
        preview = bank_batch_summary(db, UUID(order_id), matched.json(), live=False)
        assert preview["order_contribution_minor"] == 960 and preview["batch_minor"] == 1920
        assert preview["status"] == "RECONCILIATION_RECORDED"
        assert client.post(release_url, json=release_request).status_code == 401
        wrong_ack = client.post(release_url, headers=keys, json={"acknowledgment_sha256": "0" * 64})
        assert wrong_ack.status_code == 409
        release = client.post(release_url, headers=keys, json=release_request)
        assert release.status_code == 200, release.text
        assert release.json()["eligible_liability_minor"] == 1000
        assert release.json()["recognized_revenue_minor"] is None and release.json()["ledger_entry_id"] is None
        assert client.post(release_url, headers=keys, json=release_request).json() == release.json()

        from app.services.stripe_revenue_release import scoped_delivery_outcomes

        [outcome] = scoped_delivery_outcomes(db, scope, live=False)
        assert outcome["status"] == "LIABILITY_RELEASE_REHEARSED" and outcome["external_authority"] is False
        assert outcome["recognized_revenue_minor"] is None and scoped_delivery_outcomes(db, scope, live=True) == []


        assert scoped_bank_blockers(db, scope, live=False) == set()
        bank_item["transaction_id"] = "different_bank_tx"
        with pytest.raises(HTTPException, match="changed after reconciliation"):
            reconcile([order_id, other_id])
        bank_item["transaction_id"] = "test_tx_exact"

        if partial_refunds == "reversal":
            from app.banking.plaid_transactions import _posted_movement
            from app.services.stripe_bank_reversal import BankReversalIn, record_bank_reversal

            path = "/api/governance/floor/stripe-bank-batches/reversal"
            assert client.post(path, json={"payout_id": payout["id"], "reversal_id": reversing_payout["id"]}).status_code == 401
            bank_item.update(transaction_id="debit_exact", amount=19.20, payment_meta={"reference_number": "BANK-DEBIT-TEST"})
            req = BankReversalIn(payout_id=payout["id"], reversal_id=reversing_payout["id"])

            def independent_debit(**args):
                with httpx.Client(base_url="https://bank.example.invalid",
                                  transport=httpx.MockTransport(bank_upstream)) as bank_client:
                    return _posted_movement(bank_client, token="isolated", account_id="bank_test", trace=args["trace"],
                                            arrival=args["arrival"], amount_minor=args["amount_minor"],
                                            today=args["today"], debit=True)

            def correct():
                return record_bank_reversal(db, req, live=False, client=adapter, account="acct_ValhallaTest",
                                            destination="ba_ApprovedTest", bank_debit=independent_debit)

            with pytest.raises(HTTPException, match="Exact paid full"):
                correct()
            payout["reversed_by"] = reversing_payout["id"]
            bank_item["amount"] = -19.20
            with pytest.raises(HTTPException, match="differs"):
                correct()
            bank_item["amount"] = 19.20
            reversal_tx["net"] = 1919
            with pytest.raises(HTTPException, match="processor clearing"):
                correct()
            reversal_tx["net"] = 1920
            corrected = correct()
            assert corrected == correct()
            assert corrected["original_sha256"] == batch["sha256"]
            assert corrected["basis"] == "SYNTHETIC_BANK_REVERSAL"
            assert corrected["available_cash_minor"] is None and corrected["ledger_entry_id"] is None
            assert corrected["bank_debit_verified"] is False and db.query(JournalEntry).count() == 0
            assert scoped_bank_blockers(db, scope, live=False) == {"STRIPE_BANK_CORRECTION_REQUIRED"}
            return

        if partial_refunds is None:
            charge["disputed"] = True
            created = {"id": "evt_DisputeOpened", "type": "charge.dispute.created", "livemode": False,
                       "data": {"object": {**dispute, "status": "needs_response"}}}
            closed = {**created, "id": "evt_DisputeLost", "type": "charge.dispute.closed", "data": {"object": dispute}}
            assert deliver(created).status_code == 200
            assert deliver(closed).status_code == 200
            monkeypatch.setattr("app.services.stripe_dispute_correction.stripe_readback_client", read_only_fixture)
            route = f"{binding_url}/{order_id}/chargeback-correction"
            body = {"signed_event_id": closed["id"]}
            assert client.post(route, json=body).status_code == 401
            assert client.post(route, headers=keys, json={"signed_event_id": created["id"]}).status_code == 409
            dispute_tx["net"] = -1151
            assert client.post(route, headers=keys, json=body).status_code == 409
            dispute_tx["net"] = -1150
            response = client.post(route, headers=keys, json=body)
            assert response.status_code == 200, response.text
            effect = response.json()
            assert effect["debit_minor"] == 1000 and effect["fee_minor"] == 150
            assert effect["basis"] == "SYNTHETIC_CHARGEBACK" and effect["bank_debit_confirmed"] is False
            assert effect["ledger_entry_id"] is None and effect["available_cash_minor"] is None
            assert client.post(route, headers=keys, json=body).json() == effect
            won = {**closed, "id": "evt_DisputeWon", "created": int(time.time()),
                   "data": {"object": {**dispute, "status": "won"}}}
            assert deliver(won).status_code == 200
            won_request = {"signed_event_id": won["id"]}
            assert client.post(route, headers=keys, json=won_request).status_code == 409
            dispute["status"] = "won"
            dispute["balance_transactions"].append({"id": "txn_ReinstateA"})
            adjustments["/v1/balance_transactions/txn_ReinstateA"] = {
                **dispute_tx, "id": "txn_ReinstateA", "reporting_category": "dispute_reversal",
                "amount": 1000, "net": 1000, "fee": 0,
            }
            result = client.post(route, headers=keys, json=won_request)
            assert result.status_code == 200, result.text
            assert result.json()["principal_minor"] == 1000 and result.json()["returned_fee_minor"] == 0
            assert result.json()["original_chargeback_sha256"] == effect["sha256"]
            assert client.post(route, headers=keys, json=won_request).json() == result.json()
            assert db.query(JournalEntry).count() == 0
            assert scoped_bank_blockers(db, scope, live=False) == {"STRIPE_BANK_CORRECTION_REQUIRED"}
            return

        charge_b["refunded"], charge_b["amount_refunded"] = True, 1000
        signed_full_refund = {"id": "evt_FullRefundB", "type": "charge.refunded", "livemode": False, "data": {"object": {
            "id": "ch_CaptureB", "object": "charge", "amount_refunded": 1000, "currency": "cad",
            "payment_intent": "pi_CaptureB",
        }}}
        assert deliver(signed_full_refund).status_code == 200
        monkeypatch.setattr("app.services.stripe_refund_correction.stripe_readback_client", read_only_fixture)
        correction_url = f"{binding_url}/{other_id}/refund-correction"
        correction_request = {"refund_id": "re_FullB", "signed_event_id": signed_full_refund["id"]}
        assert client.post(correction_url, json=correction_request).status_code == 401
        refund_balance["fee"] = 1
        assert client.post(correction_url, headers=keys, json=correction_request).status_code == 409
        refund_balance["fee"] = 0
        corrected = client.post(correction_url, headers=keys, json=correction_request)
        assert corrected.status_code == 200, corrected.text
        assert corrected.json()["basis"] == "SYNTHETIC_REFUND_CORRECTION"
        assert corrected.json()["refund_minor"] == 1000 and corrected.json()["ledger_entry_id"] is None
        assert corrected.json()["bank_debit_confirmed"] is False and corrected.json()["cash_hold_released"] is False
        assert client.post(correction_url, headers=keys, json=correction_request).json() == corrected.json()

        if partial_refunds:
            partial_url = f"{binding_url}/{order_id}/refund-correction"
            requests = []
            for suffix, cumulative in (("PartialA", 250), ("RemainderA", 1000)):
                charge.update(refunded=cumulative == 1000, amount_refunded=cumulative)
                native_event = {"id": f"evt_{suffix}", "type": "charge.refunded", "livemode": False,
                                "data": {"object": {**charge}}}
                assert deliver(native_event).status_code == 200
                requests.append({"refund_id": f"re_{suffix}", "signed_event_id": native_event["id"]})
            assert client.post(partial_url, headers=keys, json=requests[1]).status_code == 409
            assert client.post(partial_url, headers=keys, json={
                **requests[0], "refund_id": requests[1]["refund_id"],
            }).status_code == 409
            first = client.post(partial_url, headers=keys, json=requests[0])
            assert first.status_code == 200, first.text
            from app.loki.evidence import artifact_digest
            from app.services.stripe_refund_correction import PARTIAL

            [event] = db.query(LegacyOrchestrationEvent).filter(
                LegacyOrchestrationEvent.event_id.startswith("STRIPE-RP-"),
            ).all()
            assert len(event.event_id) <= LegacyOrchestrationEvent.__table__.c.event_id.type.length

            # Older isolated stores may contain the original, longer receipt ID.
            historical = f"STRIPE-PARTIAL-REFUND-{order_id}-" + artifact_digest(
                "stripe_refund_identity", requests[0]["refund_id"], {"live": False},
            )[:32]
            envelope = json.loads(event.payload_json)
            envelope["sha256"] = artifact_digest(PARTIAL, historical, envelope["value"])
            event.event_id = historical
            event.payload_json = json.dumps(envelope)
            db.commit()

            final = client.post(partial_url, headers=keys, json=requests[1])
            assert final.status_code == 200, final.text
            assert (first.json()["refund_minor"], first.json()["cumulative_refund_minor"]) == (250, 250)
            assert (final.json()["refund_minor"], final.json()["cumulative_refund_minor"]) == (750, 1000)
            assert first.json()["bank_debit_confirmed"] is False and final.json()["available_cash_minor"] is None
            assert client.post(partial_url, headers=keys, json=requests[0]).json() == {
                **first.json(), "sha256": envelope["sha256"],
            }
            assert db.query(JournalEntry).count() == 0
            return




        failure = {"id": "evt_PayoutFailedA", "type": "payout.failed", "livemode": False, "data": {"object": {
            "id": "po_ValhallaTest", "object": "payout", "amount": 1920, "currency": "cad",
        }}}
        assert deliver(failure).status_code == 200
        [held_delivery] = scoped_delivery_outcomes(db, scope, live=False)
        assert held_delivery["status"] == "DELIVERY_REVIEW_REQUIRED"
        from app.loki.analyst import challenge
        from app.loki.evidence import artifact_digest

        report = {"status": "observed", "external_authority": False,
                  "observations": {"paid_delivery_outcomes": [held_delivery]}}
        verdict = challenge({"artifact_type": "pantheon_report", "reference": "stripe-held-delivery",
                             "raw_input": report, "artifact_sha256": artifact_digest(
                                 "pantheon_report", "stripe-held-delivery", report,
                             )})
        assert any(finding.category == "paid_delivery_evidence_review" and finding.severity == "critical"
                   for finding in verdict.findings)


        assert client.post(release_url, headers=keys, json=release_request).status_code == 409
        assert bank_batch_summary(db, UUID(order_id), matched.json(), live=False
                                  )["status"] == "CORRECTION_REVIEW_REQUIRED"
        assert scoped_bank_blockers(db, scope, live=False) == {"STRIPE_BANK_CORRECTION_REQUIRED"}
        assert scoped_bank_blockers(db, {**scope, "business_id": "another-business"}, live=False) == set()
        assert scoped_bank_blockers(db, scope, live=True) == set()
        with pytest.raises(HTTPException, match="refund hold"):
            reconcile([order_id, other_id])
        for label, type_ in (("BANK", "asset"), ("CLEARING", "asset"), ("FEES", "expense"),
                             ("OBLIGATIONS", "liability")):
            monkeypatch.setenv("VALHALLA_STRIPE_BOOK_" + label, label)
            db.add(Account(code=label, name=label, type=type_, currency="CAD", active=True))
        db.add(Period(label="test-month", start_date=posting_date, end_date=posting_date, closed=False))
        db.commit()
        entry_id = _journal(db, "isolated-fixture-booking", posting_date, scope, (1920, 80, 2000))
        db.flush()
        lines = db.query(JournalLine).filter_by(entry_id=entry_id).all()
        assert sum(line.credit for line in lines) == sum(line.debit for line in lines)
        assert len(lines) == 5
        from app.services.specialist_triggers import outcome_scope_key
        from app.services.stripe_revenue_release import _release_posting

        monkeypatch.setenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED", "1")
        monkeypatch.setenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE", outcome_scope_key(scope))
        monkeypatch.setenv("VALHALLA_STRIPE_BOOK_DELIVERY_INCOME", "DELIVERY")
        db.add(Account(code="DELIVERY", name="Paid delivery", type="income", currency="CAD", active=True))
        db.flush()
        bank_evidence = {"ledger_entry_id": entry_id, "batch_liability_minor": 2000}
        with monkeypatch.context() as scoped:
            scoped.setenv("VALHALLA_EMERGENCY_STOP", "1")
            with pytest.raises(HTTPException, match="Emergency stop holds new revenue postings") as stopped:
                _release_posting(db, "isolated-release", scope, posting_date, bank_evidence, 1000)
            assert stopped.value.status_code == 409
            assert db.query(JournalEntry).filter_by(source_ref="isolated-release").count() == 0
            scoped.setenv("VALHALLA_EMERGENCY_STOP", "0")
            with pytest.raises(HTTPException, match="Cross-period service needs a separately approved"):
                _release_posting(db, "isolated-release", scope, posting_date, bank_evidence, 1000,
                                 served_from=date(2020, 1, 1), served_until=posting_date)
            posting = _release_posting(db, "isolated-release", scope, posting_date, bank_evidence, 1000,
                                       served_from=posting_date, served_until=posting_date)
        db.flush()
        release_lines = db.query(JournalLine).filter_by(entry_id=posting).all()
        assert len(release_lines) == 2
        assert sum(line.debit for line in release_lines) == sum(line.credit for line in release_lines) == 10

        from app.services.stripe_refund_correction import _post_correction

        reversal = _post_correction(db, scope, "isolated-unrecognized-refund", posting_date, 1000,
                                    {"ledger_entry_id": entry_id, "batch_liability_minor": 2000}, None)
        db.flush()
        correction_lines = db.query(JournalLine).filter_by(entry_id=reversal).all()
        assert len(correction_lines) == 2
        assert sum(line.debit for line in correction_lines) == sum(line.credit for line in correction_lines) == 10
        assert {db.get(Account, line.account_id).code for line in correction_lines} == {"CLEARING", "OBLIGATIONS"}

        db.rollback()
        assert db.query(JournalEntry).count() == 0

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
        assert client.get(purchase, headers=buyer_headers).status_code == 409
        revoke_url = gate + "/revoke"
        reason = {"reason_reference": "fixture-license-revocation"}
        revoke = client.post(revoke_url, headers=keys, json=reason)
        assert revoke.status_code == 200 and revoke.json()["revoked"] is True
        assert client.post(revoke_url, headers=keys, json=reason).json() == revoke.json()
        assert client.post(revoke_url, headers=keys, json={"reason_reference": "different-reference"}).status_code == 409

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
        assert db.query(StripeBalanceEvidence).count() == 2
        charge["amount_refunded"] = 50
        with pytest.raises(HTTPException, match="refunded"):
            read()


def test_bank_balance_observation_holds_actual_funds_and_limits_bank_scope(deal_client, monkeypatch):
    from app.banking.plaid_transactions import account_balance_observation
    from app.services.specialist_triggers import outcome_scope_key

    client, _ = deal_client
    account_id = "fixture_bank_account"
    body = {"request_id": "fixture_plaid_request", "accounts": [{
        "account_id": account_id, "type": "depository",
        "balances": {"iso_currency_code": "CAD", "current": 10000.0, "available": 9000.01},
    }]}
    calls = []

    def upstream(request):
        calls.append(request.url.path)
        assert request.method == "POST" and request.url.path == "/accounts/balance/get"
        assert json.loads(request.content)["options"] == {"account_ids": [account_id]}
        return httpx.Response(200, json=body)

    with httpx.Client(base_url="https://bank.example.invalid", transport=httpx.MockTransport(upstream)) as bank:
        def read_balance(**kwargs):
            assert kwargs["stripe_destination"] == "ba_Balance"
            return account_balance_observation(bank, token="isolated-test", account_id=account_id, live=False)

        monkeypatch.setattr("app.banking.plaid_transactions.configured_bank_balance", read_balance)
        monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
        monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "balance-observation-test")
        monkeypatch.setenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID", "ba_Balance")
        scope = {"legacy_instance_id": "legacy-balance", "business_id": "business-balance",
                 "engine_id": "engine-balance", "jurisdiction": "CA-MB"}
        monkeypatch.setenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE", outcome_scope_key(scope))
        path = "/api/governance/floor/stripe-bank-batches/balance-observation"
        owner = {"X-Owner-Mandate-Key": "balance-observation-test"}
        assert client.post(path, json=scope).status_code == 401
        assert client.post(path, json={**scope, "business_id": "business-different"}, headers=owner).status_code == 409
        assert calls == []
        result = client.post(path, json=scope, headers=owner)
        assert result.status_code == 200 and result.headers["cache-control"] == "no-store"
        assert result.json()["bank_available_reported_minor"] == 900001
        assert result.json()["actual_accessible_funds_minor"] is None
        assert result.json()["funds_movement_authorized"] is False
        assert result.json()["basis"] == "PLAID_SANDBOX_BALANCE_OBSERVATION"
        assert account_id not in result.text and body["request_id"] not in result.text
        body["accounts"][0]["balances"]["available"] = 9000.001
        assert client.post(path, json=scope, headers=owner).status_code == 409
        body["accounts"][0]["balances"]["available"] = None
        assert client.post(path, json=scope, headers=owner).status_code == 409


def test_correction_journals_keep_original_liability_and_balance_separate_effects(deal_client, monkeypatch):
    from decimal import Decimal
    from app.accounting.models import Account, JournalLine, Period
    from app.services.specialist_triggers import outcome_scope_key
    from app.services.stripe_bank_booking import _journal
    from app.services.stripe_bank_reversal import _book_reversal
    from app.services.stripe_refund_correction import _post_correction
    from app.services.stripe_dispute_correction import SOURCE, _post_reinstatement, _record_chargeback
    from app.services.stripe_revenue_release import SOURCE as RELEASE_SOURCE

    _, engine = deal_client
    for model in (Account, Period, JournalEntry, JournalLine, LegacyOrchestrationEvent):
        model.__table__.create(engine, checkfirst=True)
    scope = {"legacy_instance_id": "legacy-books", "business_id": "accounting-fixture",
             "engine_id": "finance-books", "jurisdiction": "CA-MB"}
    monkeypatch.setenv("VALHALLA_STRIPE_BANK_BOOKING_ENABLED", "1")
    monkeypatch.setenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE", outcome_scope_key(scope))
    for name in ("BANK", "CLEARING", "FEES", "OBLIGATIONS", "REFUND_CONTRA_INCOME"):
        monkeypatch.setenv("VALHALLA_STRIPE_BOOK_" + name, name)
    booked_on = date(2026, 11, 20)
    with Session(engine) as db:
        accounts = {key: Account(code=key, name=key, type=value, currency="CAD", active=True)
                    for key, value in {"BANK": "asset", "CLEARING": "asset", "FEES": "expense",
                                       "OBLIGATIONS": "liability", "REFUND_CONTRA_INCOME": "income"}.items()}
        period = Period(label="isolated correction", start_date=booked_on, end_date=booked_on, closed=False)
        db.add_all([period, *accounts.values()])
        db.flush()
        original = _journal(db, "book_fixture", booked_on, scope, (1140, 60, 1200))
        db.flush()
        receipt = {"ledger_entry_id": original, "batch_liability_minor": 1200}
        reversal = _book_reversal(db, "book_fixture", "reverse_fixture", scope, receipt, 1140, booked_on)
        chargeback = _post_correction(db, scope, "dispute_fixture", booked_on, 1200, receipt, None,
                                      fee=150, source=SOURCE)
        db.flush()

        def amounts(entry):
            return {(line.account_id, line.debit, line.credit)
                    for line in db.query(JournalLine).filter_by(entry_id=entry)}

        assert (accounts["OBLIGATIONS"].id, 0, Decimal("12.00")) in amounts(original)
        assert amounts(reversal) == {(accounts["BANK"].id, 0, Decimal("11.40")),
                                     (accounts["CLEARING"].id, Decimal("11.40"), 0)}
        assert amounts(chargeback) == {(accounts["OBLIGATIONS"].id, Decimal("12.00"), 0),
                                       (accounts["CLEARING"].id, 0, Decimal("13.50")),
                                       (accounts["FEES"].id, Decimal("1.50"), 0)}
        release_posting = JournalEntry(entry_date=booked_on, source=RELEASE_SOURCE, source_ref="release_fixture")
        db.add(release_posting)
        db.flush()
        released = {"ledger_entry_id": release_posting.id, "recognized_revenue_minor": 1200,
                    "posting_date": booked_on.isoformat()}
        effect = {"scope": scope, "debit_minor": 475, "fee_minor": 150, "processor_balance_id": "txn_Partial",
                  "processor_posted_on": booked_on.isoformat()}
        bank = {**receipt, "booked_on": booked_on.isoformat()}
        corrected = _record_chargeback(
            db, "partial_fixture", dict(effect), bank, "release_fixture", released, captured_minor=1200, live=True,
        )
        assert amounts(corrected["ledger_entry_id"]) == {
            (accounts["REFUND_CONTRA_INCOME"].id, Decimal("4.75"), 0),
            (accounts["CLEARING"].id, 0, Decimal("6.25")),
            (accounts["FEES"].id, Decimal("1.50"), 0),
        }
        assert _record_chargeback(
            db, "partial_fixture", dict(effect), bank, "release_fixture", released, captured_minor=1200, live=True,
        ) == corrected
        restore = {"scope": scope, "returned_fee_minor": 25, "processor_posted_on": booked_on.isoformat()}
        reinstatement = _post_reinstatement(db, "won_fixture", "partial_fixture",
                                            {**corrected, "corrects_delivery_income": True}, restore)
        db.flush()
        assert amounts(reinstatement) == {
            (accounts["REFUND_CONTRA_INCOME"].id, 0, Decimal("4.75")),
            (accounts["CLEARING"].id, Decimal("5.00"), 0),
            (accounts["FEES"].id, 0, Decimal("0.25")),
        }
        assert (accounts["FEES"].id, Decimal("1.50"), 0) in amounts(corrected["ledger_entry_id"])
        period.closed = True
        with pytest.raises(HTTPException, match="open accounting period"):
            _post_reinstatement(db, "late_won_fixture", "partial_fixture",
                                {**corrected, "corrects_delivery_income": True}, restore)
        with pytest.raises(HTTPException, match="open accounting period"):
            _book_reversal(db, "book_fixture", "late_fixture", scope, receipt, 1140, booked_on)


def test_signed_cash_close_reconciles_scoped_fixture_without_movement_authority(deal_client, monkeypatch):
    from datetime import datetime, timezone
    from decimal import Decimal
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from app.accounting.models import Account, JournalLine
    from app.services.specialist_triggers import outcome_scope_key
    from app.services.treasury_cash_position import CashCloseIn, REQUIRED_PROTECTIONS, cash_close_message, journal_snapshot

    client, engine = deal_client
    scope = {"legacy_instance_id": "legacy-close", "business_id": "business-close",
             "engine_id": "engine-close", "jurisdiction": "CA-MB"}
    for model in (Account, JournalEntry, JournalLine):
        model.__table__.create(engine, checkfirst=True)
    with Session(engine) as db:
        entry = JournalEntry(entry_date=date.today(), source="fixture", source_ref="one")
        account = Account(code="cash_fixture", name="Fixture", type="asset", currency="CAD")
        offset = Account(code="capital_fixture", name="Offset fixture", type="equity", currency="CAD")
        db.add_all([entry, account, offset])
        db.flush()
        line = JournalLine(entry_id=entry.id, account_id=account.id, debit=Decimal("1000.00"), credit=0)
        db.add_all([line, JournalLine(entry_id=entry.id, account_id=offset.id, debit=0, credit=Decimal("1000.00"))])
        db.commit()
        line_id = line.id
        head, digest = journal_snapshot(db)
    signer = Ed25519PrivateKey.generate()
    public = signer.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "cash-close-fixture-mandate")
    monkeypatch.setenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE", outcome_scope_key(scope))
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "0")
    monkeypatch.setenv("VALHALLA_TREASURY_CASH_ATTESTATION_KEYS", json.dumps({"fixture-accountant": {
        "public_key_hex": public, "scope_sha256": outcome_scope_key(scope), "account_sha256": "a" * 64,
        "evidence_class": "SYNTHETIC",
    }}))
    monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
    bank = {"basis": "PLAID_SANDBOX_BALANCE_OBSERVATION", "account_reference_sha256": "a" * 64,
            "request_reference_sha256": "b" * 64, "bank_current_reported_minor": 100000,
            "bank_available_reported_minor": 90000}
    calls = []

    def read_bank(**kwargs):
        calls.append(kwargs)
        return bank

    monkeypatch.setattr("app.banking.plaid_transactions.configured_bank_balance", read_bank)
    close = {"scope": scope, "signer_id": "fixture-accountant", "signature": "0" * 128,
             "issued_at": datetime.now(timezone.utc).isoformat(), "currency": "CAD",
             "evidence_class": "SYNTHETIC", "ledger_snapshot_sha256": digest, "journal_head": head,
             "bank_current_minor": 100000, "bank_available_minor": 90000, "account_reference_sha256": "a" * 64,
             "reviewed_categories": sorted(REQUIRED_PROTECTIONS), "retained_distributable_profit_minor": 50000,
             "protections": [
                 {"category": "restricted_funds", "amount_minor": 10000, "ledger_item_sha256": "1" * 64,
                  "already_reflected_in_bank_available": True},
                 {"category": "delivery_obligations", "amount_minor": 20000, "ledger_item_sha256": "2" * 64,
                  "already_reflected_in_bank_available": False},
                 {"category": "tax_and_other_liabilities", "amount_minor": 5000, "ledger_item_sha256": "3" * 64,
                  "already_reflected_in_bank_available": False},
             ]}

    def signed(data):
        return {**data, "signature": signer.sign(cash_close_message(CashCloseIn.model_validate(data))).hex()}

    body = {"signed_close": signed(close), "allocation_preferences": {
        "essential_household_minor": 10000, "personal_reserve_target_minor": 3000,
        "personal_reserve_balance_minor": 0,
    }}
    path = "/api/governance/floor/stripe-bank-batches/cash-close"
    headers = {"X-Owner-Mandate-Key": "cash-close-fixture-mandate"}
    assert client.post(path, json=body).status_code == 401
    assert client.post(path, headers=headers, json={"signed_close": close}).status_code == 409
    duplicate = signed({**close, "protections": [*close["protections"], close["protections"][0]]})
    assert client.post(path, headers=headers, json={"signed_close": duplicate}).status_code == 409
    assert calls == []
    result = client.post(path, headers=headers, json=body)
    assert result.status_code == 200, result.text
    evidence = result.json()
    assert result.headers["cache-control"] == "no-store"
    assert evidence["actual_accessible_funds_minor"] is None and evidence["funds_movement_authorized"] is False
    assert evidence["synthetic_cash_headroom_minor"] == 65000
    assert evidence["synthetic_eligible_distribution_minor"] == 50000
    assert evidence["allocation"]["recommended_personal_minor"] == 20000
    bank["bank_available_reported_minor"] -= 1
    assert client.post(path, headers=headers, json=body).status_code == 409
    bank["bank_available_reported_minor"] += 1
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "1")
    held = client.post(path, headers=headers, json=body).json()
    assert held["blockers"] == ["EMERGENCY_STOP"] and held["allocation"] is None
    assert held["synthetic_cash_headroom_minor"] is None
    with Session(engine) as db:
        db.get(JournalLine, line_id).debit = Decimal("1000.01")
        db.commit()
    assert client.post(path, headers=headers, json=body).status_code == 409
    assert len(calls) == 3
