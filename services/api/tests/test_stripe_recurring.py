"""Recurring billing contract exercised only with isolated Stripe and subscriber fixtures."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs
from uuid import uuid4

import httpx
from sqlalchemy.orm import Session

from app.core import db as database
from app.models.auth_revocations import RevokedAccessToken
from app.models.saas_access import SaaSPlan, SaaSPlanModule, Subscription
from app.models.stripe_finance import StripeFinancialEvent
from app.models.stripe_recurring import StripePaidPeriod, StripeRecurringAttempt, StripeSaaSBinding
from app.routers.auth_weweb import _auth_runtime, _issue_access_token
from app.services.stripe_recurring import scoped_subscription_outcomes
from app.services.stripe_recurring_worker import reconcile_due_invoice
from app.users.models import AccountSettings, UserProfile


def test_recurring_checkout_renewal_cancellation_and_payment_holds(deal_client, monkeypatch):
    client, engine = deal_client
    for model in (UserProfile, AccountSettings, RevokedAccessToken, SaaSPlan, SaaSPlanModule,
                  Subscription, StripeFinancialEvent, StripeSaaSBinding, StripePaidPeriod, StripeRecurringAttempt):
        model.__table__.create(engine, checkfirst=True)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr("app.webhooks.stripe.is_live", lambda: False)
    monkeypatch.setattr("app.routers.stripe_financial.is_live", lambda: False)
    monkeypatch.setattr("app.services.stripe_recurring._check_legacy", lambda *args, **kwargs: None)
    monkeypatch.setattr("app.services.stripe_recurring.require_no_containment", lambda *args, **kwargs: None)
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    secret = "synthetic-recurring-signature"
    monkeypatch.setenv("VALHALLA_STRIPE_EVENT_MODE", "test")
    monkeypatch.setenv("VALHALLA_STRIPE_TEST_WEBHOOK_SECRET", secret)
    monkeypatch.setenv("VALHALLA_STRIPE_ACCOUNT_ID", "acct_Recurring")
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "owner-recurring-fixture")
    origin = "https://editor.example.invalid"
    monkeypatch.setenv("VALHALLA_STRIPE_RECURRING_SUCCESS_URL", origin + "/return")
    monkeypatch.setenv("VALHALLA_STRIPE_RECURRING_CANCEL_URL", origin + "/cancel")
    tenant = str(uuid4())
    with Session(engine) as db:
        people = [UserProfile(first_name="Test", last_name=name, email=f"stripe-{name}@example.invalid")
                  for name in ("subscriber", "outsider")]
        db.add_all(people)
        plan = SaaSPlan(code="recurring-test", name="Recurring plan", price_monthly=12, currency="CAD")
        db.add(plan)
        db.flush()
        for person in people:
            db.add(AccountSettings(user_id=person.user_id, account_locked=False, password_hash="isolated"))
        db.add(SaaSPlanModule(plan_id=plan.id, module_key="wholesale_engine"))
        local = Subscription(user_id=people[0].user_id, plan_id=plan.id, provider="stripe",
                             status="pending_verification")
        db.add(local)
        db.flush()
        local_id = local.id
        buyer, outsider = ({"Authorization": f"Bearer {_issue_access_token(_auth_runtime(), person)}"}
                           for person in people)
        db.commit()

    root = f"/api/governance/floor/stripe-subscriptions/{local_id}"
    owner = {"X-Owner-Mandate-Key": "owner-recurring-fixture"}
    params = {"tenant_id": tenant, "stripe_customer_id": "cus_Recurring", "stripe_price_id": "price_Month",
              "stripe_product_id": "prod_Product", "monthly_minor": 1200, "scope": {
                  "legacy_instance_id": "legacy-fixture", "business_id": "business-fixture",
                  "engine_id": "engine-fixture", "jurisdiction": "CA-MB",
              }}
    assert client.post(root + "/bind", json=params).status_code == 401
    assert client.post(root + "/bind", headers=owner, json={**params, "monthly_minor": 1300}).status_code == 409
    bound = client.post(root + "/bind", headers=owner, json=params)
    assert bound.status_code == 201, bound.text
    metadata = {"valhalla_subscription": str(local_id), "valhalla_binding_sha256": bound.json()["binding_sha256"]}
    assert client.post(root + "/bind", headers=owner, json=params).json() == bound.json()
    url = f"/api/weweb/stripe-subscriptions/{tenant}/{local_id}"
    assert client.get(url, headers=outsider).status_code == 404
    assert client.get(url, headers=buyer).json()["status"] == "NO_CURRENT_PAID_PERIOD"
    assert client.post(url + "/checkout", headers=buyer).status_code == 503

    checkout = {"id": "cs_Recurring", "object": "checkout.session", "mode": "subscription", "livemode": False,
                "customer": "cus_Recurring", "client_reference_id": str(local_id), "metadata": metadata,
                "currency": "cad", "amount_total": 1200, "status": "open",
                "url": "https://checkout.stripe.com/c/pay/test-opaque"}
    native = {"id": "sub_Recurring", "object": "subscription", "customer": "cus_Recurring", "livemode": False,
              "metadata": metadata, "currency": "cad", "collection_method": "charge_automatically", "status": "active",
              "cancel_at_period_end": False, "items": {"has_more": False, "data": [
                  {"quantity": 1, "price": {"id": "price_Month", "product": "prod_Product"}},
              ]}}
    clock = datetime.now(timezone.utc)
    start = int((clock - timedelta(days=2)).timestamp())
    end = start + 30 * 86400
    fixtures = {
        "/v1/account": {"id": "acct_Recurring", "object": "account"},
        "/v1/customers/cus_Recurring": {"id": "cus_Recurring", "object": "customer", "livemode": False},
        "/v1/products/prod_Product": {"id": "prod_Product", "object": "product", "active": True},
        "/v1/prices/price_Month": {"id": "price_Month", "object": "price", "active": True, "livemode": False,
                                  "product": "prod_Product", "currency": "cad", "type": "recurring",
                                  "billing_scheme": "per_unit", "unit_amount": 1200,
                                  "recurring": {"interval": "month", "interval_count": 1, "usage_type": "licensed"}},
        "/v1/checkout/sessions/cs_Recurring": checkout,
        "/v1/subscriptions/sub_Recurring": native,
    }
    payments = {}
    posts = []
    renewals_available = False

    def stripe(request):
        path = request.url.path
        if request.method == "POST":
            posts.append((path, request.headers["Idempotency-Key"]))
            if path == "/v1/checkout/sessions":
                fields = parse_qs(request.content.decode())
                assert fields["subscription_data[metadata][valhalla_binding_sha256]"] == [metadata["valhalla_binding_sha256"]]
                assert fields["line_items[0][price]"] == ["price_Month"]
                if len(posts) == 1:
                    return httpx.Response(503)
                return httpx.Response(200, json=checkout)
            assert path == "/v1/subscriptions/sub_Recurring"
            assert parse_qs(request.content.decode()) == {"cancel_at_period_end": ["true"]}
            native["cancel_at_period_end"] = True
            return httpx.Response(200, json=native)
        if path == "/v1/invoices/in_Renewal" and not renewals_available:
            return httpx.Response(503)
        if path == "/v1/invoice_payments":
            return httpx.Response(200, json={"has_more": False, "data": [payments[request.url.params["invoice"]]]})
        return httpx.Response(200, json=fixtures[path])

    @contextmanager
    def clients(*, live, write=False):
        assert live is False
        with httpx.Client(base_url="https://stripe.example.invalid", transport=httpx.MockTransport(stripe)) as adapter:
            yield adapter, adapter if write else None

    monkeypatch.setattr("app.routers.stripe_financial.recurring_clients", clients)
    monkeypatch.setattr("app.services.stripe_recurring._now", lambda: clock)
    assert client.post(url + "/checkout", headers=outsider).status_code == 404
    assert client.post(url + "/checkout", headers=buyer).status_code == 503
    opened = client.post(url + "/checkout", headers=buyer)
    assert opened.status_code == 200, opened.text
    assert opened.json()["checkout_status"] == "open"
    assert client.post(url + "/checkout", headers=buyer).json() == opened.json()
    assert len(posts) == 2 and posts[0] == posts[1]
    checkout.update(status="complete", subscription="sub_Recurring", url=None)

    def webhook(kind, suffix, item):
        event_id = f"evt_{suffix}"
        body = json.dumps({"id": event_id, "type": kind, "livemode": False, "data": {"object": item}}).encode()
        timestamp = str(int(time.time()))
        signature = hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        delivery = client.post("/webhooks/stripe", content=body, headers={"Stripe-Signature": f"t={timestamp},v1={signature}"})
        assert delivery.status_code == 200, delivery.text
        return {"event_id": event_id}

    def invoice(suffix, first, last):
        invoice_id, intent, charge = f"in_{suffix}", f"pi_{suffix}", f"ch_{suffix}"
        invoice_object = {"id": invoice_id, "object": "invoice", "customer": "cus_Recurring", "currency": "cad",
                          "livemode": False, "status": "paid", "collection_method": "charge_automatically",
                          "total": 1200, "amount_due": 1200, "amount_paid": 1200, "amount_remaining": 0,
                          "parent": {"subscription_details": {"subscription": "sub_Recurring", "metadata": metadata}},
                          "lines": {"has_more": False, "data": [{
                              "quantity": 1, "amount": 1200, "currency": "cad",
                              "parent": {"type": "subscription_item_details",
                                         "subscription_item_details": {"proration": False}},
                              "pricing": {"price_details": {"price": "price_Month", "product": "prod_Product"}},
                              "period": {"start": first, "end": last},
                          }]}}
        fixtures[f"/v1/invoices/{invoice_id}"] = invoice_object
        fixtures[f"/v1/payment_intents/{intent}"] = {"id": intent, "object": "payment_intent", "livemode": False,
            "status": "succeeded", "latest_charge": charge, "currency": "cad", "customer": "cus_Recurring",
            "amount_received": 1200}
        fixtures[f"/v1/charges/{charge}"] = {"id": charge, "object": "charge", "livemode": False, "currency": "cad",
            "status": "succeeded", "payment_intent": intent, "customer": "cus_Recurring", "amount_captured": 1200,
            "paid": True, "captured": True, "refunded": False, "disputed": False, "amount_refunded": 0}
        payments[invoice_id] = {"object": "invoice_payment", "invoice": invoice_id, "livemode": False, "amount_paid": 1200,
                                "currency": "cad", "status": "paid", "payment": {"type": "payment_intent",
                                                                               "payment_intent": intent}}
        return invoice_object

    first = invoice("First", start, end)
    proof = webhook("invoice.paid", "FirstPaid", first)
    payments[first["id"]]["payment"]["type"] = "charge"
    assert client.post(root + "/paid-period", headers=owner, json=proof).status_code == 409
    payments[first["id"]]["payment"]["type"] = "payment_intent"
    paid = client.post(root + "/paid-period", headers=owner, json=proof)
    assert paid.status_code == 200, paid.text
    assert client.post(root + "/paid-period", headers=owner, json=proof).json() == paid.json()
    assert client.get(url, headers=buyer).json()["paid_until"] == end
    failed_invoice = {**first, "id": "in_Renewal", "status": "open", "amount_paid": 0}
    webhook("invoice.payment_failed", "FailedRenewal", failed_invoice)
    recovery = client.get(url, headers=buyer).json()
    assert recovery["status"] == "PAID" and recovery["collection_status"] == "PAYMENT_RECOVERY"
    renewed = invoice("Renewal", end, end + 30 * 86400)
    proof = webhook("invoice.paid", "Renewed", renewed)
    with Session(engine) as db, clients(live=False) as (reader, _):
        assert reconcile_due_invoice(db, reader, live=False, now=clock) == {"status": "retry_pending", "attempts": 1}
        assert reconcile_due_invoice(db, reader, live=False, now=clock) == {"status": "idle"}
        renewals_available = True
        assert reconcile_due_invoice(db, reader, live=False, now=clock + timedelta(seconds=31)) == {
            "status": "recorded", "basis": "STRIPE_TEST_PAID_PERIOD",
        }
        assert reconcile_due_invoice(db, reader, live=False, now=clock + timedelta(seconds=31)) == {"status": "idle"}
    renewal = client.post(root + "/paid-period", headers=owner, json=proof)
    assert renewal.status_code == 200, renewal.text
    assert client.get(url, headers=buyer).json()["collection_status"] == "NO_UNRESOLVED_FAILURE"
    clock = datetime.fromtimestamp(end + 1, timezone.utc)
    canceled = client.post(url + "/cancel-at-period-end", headers=buyer)
    assert canceled.status_code == 200, canceled.text
    assert canceled.json()["cancel_at_period_end"] and canceled.json()["status"] == "PAID"
    assert canceled.json()["modules"] == [] and canceled.json()["available_cash_minor"] is None
    assert client.post(url + "/cancel-at-period-end", headers=buyer).json() == canceled.json()
    assert len(posts) == 3
    with Session(engine) as db:
        summary = scoped_subscription_outcomes(db, params["scope"], live=False)
        assert summary["verified_current_periods"] == summary["verified_adjacent_renewals"] == 1
        assert summary["scheduled_cancellations"] == 1 and summary["recognized_revenue_minor"] is None
        assert scoped_subscription_outcomes(db, {**params["scope"], "business_id": "other"}, live=False) is None
        assert scoped_subscription_outcomes(db, params["scope"], live=True) is None
    clock = datetime.fromtimestamp(end + 30 * 86400, timezone.utc)
    assert client.get(url, headers=buyer).json()["status"] == "NO_CURRENT_PAID_PERIOD"
    clock = datetime.fromtimestamp(end + 1, timezone.utc)
    webhook("charge.refunded", "RenewalRefund", {"id": "ch_Renewal", "object": "charge",
            "currency": "cad", "amount_refunded": 200, "payment_intent": "pi_Renewal"})
    assert client.get(url, headers=buyer).json()["status"] == "EVIDENCE_HELD"
    with Session(engine) as db:
        assert db.query(StripePaidPeriod).count() == 2
        held = scoped_subscription_outcomes(db, params["scope"], live=False)
        assert held["status"] == "REVIEW_REQUIRED" and held["available_cash_minor"] is None
    from app.loki.analyst import challenge
    from app.loki.evidence import artifact_digest

    report = {"status": "observed", "external_authority": False, "observations": {"recurring_paid_periods": held}}
    verdict = challenge({"artifact_type": "pantheon_report", "reference": "stripe-recurring-hold", "raw_input": report,
                         "artifact_sha256": artifact_digest("pantheon_report", "stripe-recurring-hold", report)})
    assert any(item.category == "recurring_payment_evidence_review" and item.severity == "critical"
               for item in verdict.findings)
