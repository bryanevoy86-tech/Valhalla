"""Owner-bound one-price CAD monthly Stripe subscriptions."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import os
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import HTTPException
from pydantic import Field, field_validator
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.services.launch_readiness import require_channel_release
from app.integrations.stripe import CHARGE_CORRECTION_EVENTS
from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.saas_access import SaaSPlan, SaaSPlanModule, Subscription
from app.models.stripe_finance import StripeBalanceEvidence, StripeFinancialEvent, StripeOrderBinding
from app.models.stripe_recurring import StripePaidPeriod, StripeSaaSBinding
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.economic_control import require_no_containment
from app.services.prime_business_execution import _check_legacy, _emergency_stop_active, _event, _json
from app.services.stripe_finance import (
    _event_receipt, _provider_object, capture_evidence, minor_amount, provider_json, read_captured_charge,
    read_processor_balance,
    stripe_id, stripe_readback_client,
)
from app.services.stripe_fulfillment import _buyer
from app.services.stripe_orders import _require_configured_mode
from app.services.stripe_payout_evidence import payout_membership

ALLOWED_MODULES = {"wholesale_engine", "dispo_engine"}
STRIPE_VERSION = "2025-03-31.basil"


class RecurringBindingIn(StrictModel):
    tenant_id: UUID
    stripe_customer_id: str
    stripe_price_id: str
    stripe_product_id: str
    monthly_minor: int = Field(strict=True, gt=0, le=10_000_000)
    scope: MarketScope

    @field_validator("stripe_customer_id", "stripe_price_id", "stripe_product_id")
    @classmethod
    def native_id(cls, value, info):
        prefixes = {"stripe_customer_id": "cus", "stripe_price_id": "price", "stripe_product_id": "prod"}
        if not stripe_id(value, prefixes[info.field_name]):
            raise ValueError("A native Stripe reference is required")
        return value


class InvoiceProofIn(StrictModel):
    event_id: str

    @field_validator("event_id")
    @classmethod
    def native_event(cls, value):
        if not stripe_id(value, "evt"):
            raise ValueError("A native Stripe event is required")
        return value


def _now():
    return datetime.now(timezone.utc)


def _aware(value):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _ready(db):
    inspector = inspect(db.connection())
    if not all(inspector.has_table(model.__tablename__) for model in (
        StripeSaaSBinding, StripePaidPeriod, StripeFinancialEvent,
    )):
        raise HTTPException(503, "Recurring Stripe evidence schema unavailable")


def _commit(db, detail):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail) from None


def _plan(db, local):
    plan = db.get(SaaSPlan, local.plan_id)
    modules = sorted(set(db.scalars(select(SaaSPlanModule.module_key).filter_by(plan_id=local.plan_id))))
    try:
        monthly = Decimal(str(plan.price_monthly)) * 100 if plan is not None else Decimal(0)
    except InvalidOperation:
        monthly = Decimal(0)
    if (plan is None or not plan.is_active or plan.currency != "CAD" or not modules
            or not set(modules) <= ALLOWED_MODULES or not monthly.is_finite()
            or monthly <= 0 or monthly != monthly.to_integral_value()):
        raise HTTPException(409, "An active supported CAD monthly plan is required")
    return int(monthly), modules


def _snapshot(row):
    data = row.binding
    if (not isinstance(data, dict) or data.get("subscription_id") != row.id or data.get("plan_id") != row.plan_id
            or data.get("livemode") is not row.livemode or data.get("tenant_id") != str(row.tenant_id)
            or row.binding_sha256 != artifact_digest("stripe_saas_binding", str(row.id), data)):
        raise HTTPException(409, "Subscription binding integrity check failed")
    return data


def _binding(db, local_id, live, *, lock=False):
    account = _require_configured_mode(live)
    _ready(db)
    row = db.get(StripeSaaSBinding, local_id, with_for_update=lock)
    if row is None or row.livemode is not live:
        raise HTTPException(404, "Stripe subscription unavailable")
    data = _snapshot(row)
    local = db.get(Subscription, local_id)
    if (account != data["stripe_account_id"] or local is None or local.user_id != data["subscriber_id"]
            or local.plan_id != row.plan_id or local.provider != "stripe" or local.provider_sub_id is not None
            or local.status != "pending_verification"):
        raise HTTPException(409, "Local SaaS subscription or provider binding changed")
    return row, data, local


def bind_recurring(db, local_id, request, *, live):
    account = _require_configured_mode(live)
    _ready(db)
    local = db.get(Subscription, local_id, with_for_update=True)
    if (local is None or local.provider != "stripe" or local.provider_sub_id is not None
            or local.status != "pending_verification" or _buyer(db, local.user_id) is None):
        raise HTTPException(409, "A pending Stripe subscription and active subscriber are required")
    monthly, modules = _plan(db, local)
    if monthly != request.monthly_minor:
        raise HTTPException(409, "Approved Stripe price differs from the local plan")
    scope = request.scope.model_dump()
    _check_legacy(db, **scope)
    value = {**request.model_dump(mode="json"), "subscription_id": local.id, "subscriber_id": local.user_id,
             "plan_id": local.plan_id, "modules": modules, "stripe_account_id": account, "livemode": live}
    digest = artifact_digest("stripe_saas_binding", str(local.id), value)
    prior = db.get(StripeSaaSBinding, local.id)
    if prior is not None:
        if _snapshot(prior) != value:
            raise HTTPException(409, "Subscription already has different exact terms")
    else:
        db.add(StripeSaaSBinding(id=local.id, tenant_id=request.tenant_id, plan_id=local.plan_id, livemode=live,
                                binding=value, binding_sha256=digest))
        _commit(db, "Tenant plan or subscription is already bound")
    return {"subscription_id": local.id, "tenant_id": str(request.tenant_id), "binding_sha256": digest,
            "payment_verified": False, "available_cash_minor": None}


def _subscriber(db, data, tenant_id, principal):
    actor = principal.get("user_id")
    profile = _buyer(db, actor) if type(actor) is int else None
    if (profile is None or profile.email != principal.get("sub") or actor != data["subscriber_id"]
            or str(tenant_id) != data["tenant_id"]):
        raise HTTPException(404, "Stripe subscription unavailable")


def _metadata(row):
    return {"valhalla_subscription": str(row.id), "valhalla_binding_sha256": row.binding_sha256}


def _list(obj, size):
    items = obj.get("data") if isinstance(obj, dict) else None
    if (not isinstance(items, list) or len(items) != size or obj.get("has_more") is not False
            or any(not isinstance(item, dict) for item in items)):
        raise HTTPException(409, "Stripe returned incomplete or unsupported item evidence")
    return items


def _catalog(client, data):
    _provider_object(client, "/v1/account", data["stripe_account_id"], "account")
    customer = data["stripe_customer_id"]
    if _provider_object(client, f"/v1/customers/{customer}", customer, "customer").get("livemode") is not data["livemode"]:
        raise HTTPException(409, "Stripe customer mode mismatch")
    product = data["stripe_product_id"]
    if _provider_object(client, f"/v1/products/{product}", product, "product").get("active") is not True:
        raise HTTPException(409, "Stripe product is inactive")
    price = data["stripe_price_id"]
    evidence = _provider_object(client, f"/v1/prices/{price}", price, "price")
    recurring = evidence.get("recurring") or {}
    if (evidence.get("active") is not True or evidence.get("livemode") is not data["livemode"]
            or evidence.get("product") != product or evidence.get("currency") != "cad"
            or evidence.get("type") != "recurring" or evidence.get("billing_scheme") != "per_unit"
            or not minor_amount(evidence.get("unit_amount")) or evidence["unit_amount"] != data["monthly_minor"]
            or not isinstance(recurring, dict) or recurring.get("interval") != "month"
            or recurring.get("interval_count") != 1 or recurring.get("usage_type") != "licensed"):
        raise HTTPException(409, "Stripe price differs from exact approved monthly terms")


def _posted(client, path, values, idempotency_key):
    try:
        response = client.post(path, data=values, headers={"Idempotency-Key": idempotency_key})
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, "Stripe mutation outcome is unconfirmed; use the same request") from None
    if not isinstance(result, dict):
        raise HTTPException(409, "Unexpected Stripe mutation response")
    return result


def _https(url, expected_host=None):
    if not isinstance(url, str):
        return False
    try:
        address = urlsplit(url)
        return (address.scheme == "https" and address.hostname is not None and not address.username
                and not address.password and not address.fragment and
                (expected_host is None or (address.hostname == expected_host and address.port in (None, 443))))
    except ValueError:
        return False


def _checkout_matches(row, data, response):
    if (not stripe_id(response.get("id"), "cs") or response.get("object") != "checkout.session"
            or response.get("mode") != "subscription" or response.get("livemode") is not row.livemode
            or response.get("customer") != data["stripe_customer_id"]
            or response.get("client_reference_id") != str(row.id)
            or response.get("metadata") != _metadata(row)
            or response.get("currency") != "cad" or response.get("amount_total") != data["monthly_minor"]):
        raise HTTPException(409, "Checkout session differs from the commissioned subscription")


def start_checkout(db, local_id, tenant_id, principal, *, live, reader, writer, success_url, cancel_url):
    require_channel_release("recurring_service", live=live)
    row, data, local = _binding(db, local_id, live, lock=True)
    _subscriber(db, data, tenant_id, principal)
    if row.checkout_session_id is not None:
        identity = row.checkout_session_id
        checkout = _provider_object(reader, f"/v1/checkout/sessions/{identity}", identity, "checkout.session")
    else:
        if _emergency_stop_active(db):
            raise HTTPException(503, "Subscription checkout is paused")
        scope = data["scope"]
        _check_legacy(db, **scope)
        require_no_containment(db, scope)
        if _plan(db, local) != (data["monthly_minor"], data["modules"]):
            raise HTTPException(409, "Subscription plan has changed")
        if not _https(success_url) or not _https(cancel_url):
            raise HTTPException(503, "Checkout return URLs are unconfigured")
        _catalog(reader, data)
        now = _now()
        if row.checkout_started_at is None:
            row.checkout_started_at = now
            db.commit()
            row, data, _ = _binding(db, local_id, live, lock=True)
        identity = row.checkout_session_id
        if identity:
            checkout = _provider_object(reader, f"/v1/checkout/sessions/{identity}", identity, "checkout.session")
        else:
            if _emergency_stop_active(db):
                raise HTTPException(503, "Subscription checkout is paused")
            _check_legacy(db, **data["scope"])
            require_no_containment(db, data["scope"])
            if not timedelta(0) <= now - _aware(row.checkout_started_at) < timedelta(hours=23):
                raise HTTPException(409, "Unconfirmed checkout left the safe retry window; reconcile the native session")
            terms = _metadata(row)
            values = {"mode": "subscription", "customer": data["stripe_customer_id"], "client_reference_id": str(local_id),
                      "line_items[0][price]": data["stripe_price_id"], "line_items[0][quantity]": "1",
                      "success_url": success_url, "cancel_url": cancel_url}
            for key, value in terms.items():
                values[f"metadata[{key}]"] = value
                values[f"subscription_data[metadata][{key}]"] = value
            checkout = _posted(writer, "/v1/checkout/sessions", values, "valhalla-saas-" + row.binding_sha256)
            _checkout_matches(row, data, checkout)
            row.checkout_session_id = checkout["id"]
            _commit(db, "Subscription checkout identity already in use")
    _checkout_matches(row, data, checkout)
    status = checkout.get("status")
    url = checkout.get("url") if status == "open" else None
    if status not in {"open", "complete", "expired"} or (status == "open" and not _https(url, "checkout.stripe.com")):
        raise HTTPException(409, "Unsupported hosted checkout state")
    return {"subscription_id": local_id, "checkout_status": status, "checkout_url": url,
            "basis": "STRIPE_LIVE_CHECKOUT" if live else "STRIPE_TEST_CHECKOUT", "payment_verified": False}


def _native_subscription(client, subscription_id, row, data):
    subscription = _provider_object(client, f"/v1/subscriptions/{subscription_id}", subscription_id, "subscription")
    [item] = _list(subscription.get("items"), 1)
    price = item.get("price")
    if (subscription.get("customer") != data["stripe_customer_id"] or subscription.get("livemode") is not row.livemode
            or subscription.get("metadata") != _metadata(row) or subscription.get("currency") != "cad"
            or subscription.get("collection_method") != "charge_automatically" or item.get("quantity") != 1
            or not isinstance(price, dict) or (price.get("id"), price.get("product")) != (
                data["stripe_price_id"], data["stripe_product_id"],
            )):
        raise HTTPException(409, "Stripe subscription differs from exact approved terms")
    return subscription


def _paid_invoice(client, row, data, event):
    invoice_id = event["object_id"]
    invoice = _provider_object(client, f"/v1/invoices/{invoice_id}", invoice_id, "invoice")
    parent = invoice.get("parent") or {}
    subscription_id = (parent.get("subscription_details") or {}).get("subscription") if isinstance(parent, dict) else None
    gross = data["monthly_minor"]
    if (not stripe_id(subscription_id, "sub") or event["subscription_id"] != subscription_id
            or invoice.get("customer") != data["stripe_customer_id"] or event["stripe_customer_id"] != invoice["customer"]
            or invoice.get("currency") != "cad" or invoice.get("livemode") is not row.livemode
            or invoice.get("status") != "paid" or invoice.get("collection_method") != "charge_automatically"
            or event["amount_minor"] != gross
            or any(type(invoice.get(key)) is not int or invoice[key] != gross for key in ("total", "amount_due", "amount_paid"))
            or invoice.get("amount_remaining") != 0):
        raise HTTPException(409, "Stripe invoice is unpaid or does not match the agreed CAD subscription")
    [line] = _list(invoice.get("lines"), 1)
    line_parent, pricing = line.get("parent") or {}, line.get("pricing") or {}
    subscription_line = line_parent.get("subscription_item_details") or {}
    price = pricing.get("price_details") or {}
    period = line.get("period") or {}
    start, end = period.get("start"), period.get("end")
    if (line.get("quantity") != 1 or line.get("currency") != "cad" or line.get("amount") != gross
            or line_parent.get("type") != "subscription_item_details" or subscription_line.get("proration") is not False
            or (price.get("price"), price.get("product")) != (data["stripe_price_id"], data["stripe_product_id"])
            or type(start) is not int or type(end) is not int or not 0 < start < end < 4_102_444_800
            or not 26 * 86400 <= end - start <= 32 * 86400):
        raise HTTPException(409, "Invoice line is outside the bounded monthly plan")
    [payment] = _list(provider_json(client, "/v1/invoice_payments", params={"invoice": invoice_id, "limit": 2}), 1)
    native = payment.get("payment") or {}
    intent = native.get("payment_intent")
    if (payment.get("object") != "invoice_payment" or payment.get("invoice") != invoice_id
            or payment.get("livemode") is not row.livemode or payment.get("status") != "paid"
            or payment.get("amount_paid") != gross or payment.get("currency") != "cad"
            or native.get("type") != "payment_intent" or not stripe_id(intent, "pi")):
        raise HTTPException(409, "Invoice lacks one verified native PaymentIntent")
    capture = _provider_object(client, f"/v1/payment_intents/{intent}", intent, "payment_intent")
    charge = capture.get("latest_charge")
    if (capture.get("livemode") is not row.livemode or capture.get("customer") != data["stripe_customer_id"]
            or capture.get("status") != "succeeded" or capture.get("amount_received") != gross
            or capture.get("currency") != "cad" or not stripe_id(charge, "ch")):
        raise HTTPException(409, "Invoice PaymentIntent did not capture the exact amount")
    read_captured_charge(client, data["stripe_account_id"], {"kind": "payment_intent.succeeded", "charge_id": charge,
                        "livemode": row.livemode, "payment_intent_id": intent, "currency": "cad",
                        "amount_minor": gross, "stripe_customer_id": data["stripe_customer_id"]})
    return {"invoice_id": invoice_id, "provider_subscription_id": subscription_id, "payment_intent_id": intent,
            "charge_id": charge, "period_start": start, "period_end": end, "captured_minor": gross}


def _reversed(db, row, receipt):
    snapshot = StripeFinancialEvent.snapshot
    event = db.scalar(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == row.livemode,
        snapshot["kind"].as_string().in_(CHARGE_CORRECTION_EVENTS),
        (snapshot["payment_intent_id"].as_string() == receipt["payment_intent_id"])
        | (snapshot["charge_id"].as_string() == receipt["charge_id"]),
    ).limit(1))
    if event is None:
        return False
    _event_receipt(event, True)
    return True


def _period_value(row, period):
    value = period.evidence
    if (not isinstance(value, dict) or value.get("binding_sha256") != row.binding_sha256
            or value.get("provider_subscription_id") != row.provider_subscription_id
            or (value.get("invoice_id"), value.get("payment_intent_id"), value.get("period_start"),
                value.get("period_end")) != (period.invoice_id, period.payment_intent_id,
                                            period.period_start, period.period_end)
            or period.evidence_sha256 != artifact_digest("stripe_saas_paid_period", period.invoice_id, value)):
        raise HTTPException(409, "Paid subscription evidence failed integrity")
    return value


def apply_paid_invoice(db, local_id, request, *, live, client):
    row, data, _ = _binding(db, local_id, live, lock=True)
    event = db.get(StripeFinancialEvent, request.event_id)
    if event is None or event.livemode is not live:
        raise HTTPException(404, "Signed Stripe invoice event unavailable")
    _event_receipt(event, True)
    if event.snapshot.get("kind") != "invoice.paid" or not row.checkout_session_id:
        raise HTTPException(409, "Paid invoice and exact hosted checkout evidence are required")
    evidence = _paid_invoice(client, row, data, event.snapshot)
    checkout_id = row.checkout_session_id
    checkout = _provider_object(client, f"/v1/checkout/sessions/{checkout_id}", checkout_id, "checkout.session")
    _checkout_matches(row, data, checkout)
    native = evidence["provider_subscription_id"]
    if (checkout.get("subscription") != native or checkout.get("status") != "complete"
            or row.provider_subscription_id not in (None, native)):
        raise HTTPException(409, "Invoice subscription differs from the completed checkout")
    subscription = _native_subscription(client, native, row, data)
    if _reversed(db, row, evidence):
        raise HTTPException(409, "Paid invoice is held for refund or dispute review")
    value = {**evidence, "binding_sha256": row.binding_sha256, "basis": "STRIPE_LIVE_PAID_PERIOD" if live else "STRIPE_TEST_PAID_PERIOD",
             "available_cash_minor": None, "recognized_revenue_minor": None}
    invoice_id = evidence["invoice_id"]
    prior = db.get(StripePaidPeriod, invoice_id)
    if prior is not None:
        if prior.binding_id != row.id or _period_value(row, prior) != value:
            raise HTTPException(409, "Stripe invoice already has different paid-period evidence")
        return {**value, "sha256": prior.evidence_sha256}
    overlaps = db.scalar(select(StripePaidPeriod.invoice_id).where(
        StripePaidPeriod.binding_id == row.id, StripePaidPeriod.period_start < evidence["period_end"],
        StripePaidPeriod.period_end > evidence["period_start"],
    ).limit(1))
    if overlaps is not None:
        raise HTTPException(409, "Paid periods cannot overlap")
    row.provider_subscription_id = native
    if subscription.get("cancel_at_period_end") is True or subscription.get("status") == "canceled":
        row.cancel_scheduled = True
    digest = artifact_digest("stripe_saas_paid_period", invoice_id, value)
    db.add(StripePaidPeriod(invoice_id=invoice_id, binding_id=row.id, payment_intent_id=evidence["payment_intent_id"],
                            period_start=evidence["period_start"], period_end=evidence["period_end"],
                            evidence=value, evidence_sha256=digest))
    _commit(db, "Invoice, capture or paid period already belongs to a subscription")
    return {**value, "sha256": digest}


def _period_capture(db, local_id, invoice_id, capture_event_id, *, live):
    if not stripe_id(invoice_id, "in") or not stripe_id(capture_event_id, "evt"):
        raise HTTPException(422, "Native invoice and capture event identities required")
    row, data, _ = _binding(db, local_id, live, lock=True)
    period = db.get(StripePaidPeriod, invoice_id)
    if period is None or period.binding_id != row.id:
        raise HTTPException(404, "Paid invoice unavailable for this subscription")
    value = _period_value(row, period)
    event = db.get(StripeFinancialEvent, capture_event_id)
    if event is None or event.livemode is not live:
        raise HTTPException(404, "Signed capture unavailable")
    _event_receipt(event, True)
    signed = event.snapshot
    expected = {
        "kind": "payment_intent.succeeded", "payment_intent_id": value["payment_intent_id"],
        "charge_id": value["charge_id"], "currency": "cad", "amount_minor": value["captured_minor"],
        "stripe_customer_id": data["stripe_customer_id"], "merchant_order_id": None,
    }
    if any(signed.get(key) != field for key, field in expected.items()) or _reversed(db, row, value):
        raise HTTPException(409, "Signed capture differs from the exact paid period or requires reversal review")
    if not inspect(db.connection()).has_table(StripeOrderBinding.__tablename__):
        raise HTTPException(503, "The canonical one-time order index is unavailable")
    if db.scalar(select(StripeOrderBinding.id).filter_by(
        livemode=live, payment_intent_id=value["payment_intent_id"],
    )) is not None:
        raise HTTPException(409, "The exact capture is already bound to a one-time order")
    return row, data, period, event


def verify_period_processor_balance(db, local_id, invoice_id, capture_event_id, *, live, client):
    """Attach canonical processor evidence to an exact recurring capture."""
    _, data, period, _ = _period_capture(db, local_id, invoice_id, capture_event_id, live=live)
    result = read_processor_balance(db, capture_event_id, client=client, account_id=data["stripe_account_id"], live=live)
    return {**result, "invoice_id": invoice_id, "paid_period_sha256": period.evidence_sha256,
            "recognized_revenue_minor": None, "available_cash_minor": None}


def _period_payout_evidence(db, local_id, invoice_id, payout_id, *, live, client, destination_id):
    """Record exact recurring payout membership before separate bank reconciliation."""
    if not stripe_id(invoice_id, "in") or not stripe_id(payout_id, "po"):
        raise HTTPException(422, "Native invoice and payout identities required")
    if not stripe_id(destination_id, "ba"):
        raise HTTPException(503, "Stripe payout destination is unconfigured")
    inspector = inspect(db.connection())
    _ready(db)
    if not all(inspector.has_table(model.__tablename__) for model in (StripeBalanceEvidence, LegacyOrchestrationEvent)):
        raise HTTPException(503, "Payout evidence journal unavailable")
    candidate = db.get(StripePaidPeriod, invoice_id)
    if candidate is None or candidate.binding_id != local_id:
        raise HTTPException(404, "Paid invoice unavailable for this subscription")
    recorded = db.scalar(select(StripeBalanceEvidence).filter_by(
        payment_intent_id=candidate.payment_intent_id, livemode=live,
    ))
    if recorded is None:
        raise HTTPException(409, "Recurring processor balance must be verified first")
    row, data, period, event = _period_capture(db, local_id, invoice_id, recorded.event_id, live=live)
    capture = capture_evidence(client, data["stripe_account_id"], event.snapshot, _now())
    balance = {**capture, "event_snapshot_sha256": event.snapshot_sha256}
    if (recorded.evidence != balance or recorded.balance_transaction_id != capture["balance_transaction_id"]
            or recorded.evidence_sha256 != artifact_digest("stripe_balance_evidence", event.event_id, balance)):
        raise HTTPException(409, "Current capture differs from recorded processor evidence")
    from app.services.stripe_bank_booking import _payout_failed

    if _payout_failed(db, payout_id, live):
        raise HTTPException(409, "Signed payout failure requires separate correction")
    match = payout_membership(client, payout_id, destination_id, capture, live=live)
    scope = data["scope"]
    value = {
        "scope": scope, "subscription_binding_sha256": row.binding_sha256,
        "invoice_id": invoice_id, "paid_period_sha256": period.evidence_sha256,
        "balance_evidence_sha256": recorded.evidence_sha256, "capture_net_minor": capture["net_minor"],
        "currency": "CAD", **match,
        "basis": "STRIPE_LIVE_RECURRING_PAYOUT_MEMBERSHIP" if live else "STRIPE_TEST_RECURRING_PAYOUT_MEMBERSHIP",
        "bank_settlement_verified": False, "available_cash_minor": None, "ledger_posting_created": False,
    }
    kind = "STRIPE_RECURRING_PROCESSOR_PAYOUT_MATCHED"
    reference = "STRIPE-RECURRING-PAYOUT-" + artifact_digest(kind, invoice_id, {"livemode": live})[:40]
    receipt = {**value, "sha256": artifact_digest(kind, reference, value)}
    prior = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=reference))
    if prior is not None and (prior.event_type != kind or prior.legacy_instance_id != scope["legacy_instance_id"]
                              or _json(prior.payload_json, {}) != receipt):
        raise HTTPException(409, "Paid period already has different payout evidence")
    return reference, kind, receipt, capture, prior


def verify_period_payout(db, local_id, invoice_id, payout_id, *, live, client, destination_id):
    reference, kind, receipt, _, prior = _period_payout_evidence(
        db, local_id, invoice_id, payout_id, live=live, client=client, destination_id=destination_id,
    )
    if prior is None:
        _event(db, event_id=reference, legacy_instance_id=receipt["scope"]["legacy_instance_id"], event_type=kind,
               message="Recurring capture matched exact Stripe processor payout", payload=receipt)
        _commit(db, "Payout evidence already exists; retry the exact readback")
    return receipt


def subscription_status(db, local_id, tenant_id, principal, *, live, now=None):
    row, data, local = _binding(db, local_id, live)
    _subscriber(db, data, tenant_id, principal)
    current = int((now or _now()).timestamp())
    plan = db.get(SaaSPlan, local.plan_id)
    plan_current = bool(plan and plan.is_active and set(data["modules"]) <= ALLOWED_MODULES)
    period = db.scalar(select(StripePaidPeriod).where(
        StripePaidPeriod.binding_id == row.id, StripePaidPeriod.period_start <= current, StripePaidPeriod.period_end > current,
    ).order_by(StripePaidPeriod.period_start.desc()).limit(1))
    intact = period is not None and not _reversed(db, row, _period_value(row, period))
    state = "PAID" if intact and plan_current else "EVIDENCE_HELD" if period is not None else "NO_CURRENT_PAID_PERIOD"
    snapshot = StripeFinancialEvent.snapshot
    native = row.provider_subscription_id
    events = db.scalars(select(StripeFinancialEvent).where(
        StripeFinancialEvent.livemode == live, snapshot["subscription_id"].as_string() == native,
        snapshot["stripe_customer_id"].as_string() == data["stripe_customer_id"],
        snapshot["kind"].as_string().in_(("customer.subscription.deleted", "invoice.payment_failed")),
    )).all() if native else []
    failed_unrecovered = False
    canceled = row.cancel_scheduled
    for event in events:
        _event_receipt(event, True)
        if event.snapshot["kind"] == "customer.subscription.deleted":
            canceled = True
        elif db.get(StripePaidPeriod, event.snapshot["object_id"]) is None:
            failed_unrecovered = True
    return {"subscription_id": local_id, "tenant_id": str(tenant_id), "status": state,
            "basis": "STRIPE_LIVE_SUBSCRIPTION" if live else "STRIPE_TEST_SUBSCRIPTION",
            "paid_until": period.period_end if intact else None,
            "cancel_at_period_end": canceled, "collection_status": "PAYMENT_RECOVERY" if failed_unrecovered else "NO_UNRESOLVED_FAILURE",
            "modules": data["modules"] if live and state == "PAID" else [],
            "available_cash_minor": None, "recognized_revenue_minor": None}


def subscriber_recurring_list(db, tenant_id, principal, *, live, before=None):
    """Return only the current subscriber's own contracts for the selected tenant."""
    actor = principal.get("user_id")
    profile = _buyer(db, actor) if type(actor) is int else None
    if profile is None or profile.email != principal.get("sub"):
        raise HTTPException(404, "Stripe subscription unavailable")
    _require_configured_mode(live)
    _ready(db)
    query = (select(StripeSaaSBinding.id).join(Subscription, Subscription.id == StripeSaaSBinding.id)
             .where(Subscription.user_id == actor, StripeSaaSBinding.tenant_id == tenant_id,
                    StripeSaaSBinding.livemode == live))
    if before is not None:
        query = query.where(StripeSaaSBinding.id < before)
    ids = db.scalars(query.order_by(StripeSaaSBinding.id.desc()).limit(21)).all()
    statuses = []
    fields = ("subscription_id", "status", "basis", "paid_until", "cancel_at_period_end", "collection_status")
    for local_id in ids[:20]:
        # Revalidate each immutable buyer binding and use the exact same effective-state
        # computation as the individually addressed status route.
        status = subscription_status(db, local_id, tenant_id, principal, live=live)
        statuses.append({key: status[key] for key in fields})
    return {"tenant_id": str(tenant_id), "subscriptions": statuses,
            "next_before": ids[19] if len(ids) == 21 else None, "external_effects": 0}


def schedule_cancellation(db, local_id, tenant_id, principal, *, live, reader, writer):
    require_channel_release("recurring_service", live=live)
    row, data, _ = _binding(db, local_id, live, lock=True)
    _subscriber(db, data, tenant_id, principal)
    subscription_id = row.provider_subscription_id
    if not stripe_id(subscription_id, "sub"):
        raise HTTPException(409, "No verified native subscription to cancel")
    _provider_object(reader, "/v1/account", data["stripe_account_id"], "account")
    existing = _native_subscription(reader, subscription_id, row, data)
    if existing.get("cancel_at_period_end") is not True and existing.get("status") != "canceled":
        if _emergency_stop_active(db):
            raise HTTPException(503, "Subscription cancellation transport is paused")
        changed = _posted(writer, f"/v1/subscriptions/{subscription_id}", {"cancel_at_period_end": "true"},
                          "valhalla-saas-cancel-" + row.binding_sha256)
        if changed.get("id") != subscription_id or changed.get("cancel_at_period_end") is not True:
            raise HTTPException(409, "Stripe did not confirm period-end cancellation")
        existing = _native_subscription(reader, subscription_id, row, data)
        if existing.get("cancel_at_period_end") is not True and existing.get("status") != "canceled":
            raise HTTPException(409, "Period-end cancellation is not independently confirmed")
    row.cancel_scheduled = True
    db.commit()
    return subscription_status(db, local_id, tenant_id, principal, live=live)


@contextmanager
def recurring_clients(*, live, write=False):
    if write:
        require_channel_release("recurring_service", live=live)
        mode = "live" if live else "test"
        key = os.getenv("VALHALLA_STRIPE_RECURRING_WRITE_KEY", "")
        if os.getenv("VALHALLA_STRIPE_RECURRING_WRITE_MODE") != mode or not key.startswith(f"rk_{mode}_"):
            raise HTTPException(503, "Stripe recurring mutations are disabled or unconfigured")
    with stripe_readback_client(live=live) as (reader, _):
        reader.headers["Stripe-Version"] = STRIPE_VERSION
        if not write:
            yield reader, None
            return
        with httpx.Client(base_url="https://api.stripe.com", auth=(key, ""),
                          headers={"Stripe-Version": STRIPE_VERSION}, follow_redirects=False,
                          timeout=5.0, trust_env=False) as writer:
            yield reader, writer



def paid_module_access(db, tenant_id, module_key, principal, *, live):
    if not live or os.getenv("VALHALLA_STRIPE_EVENT_MODE") != "live" or not inspect(
        db.connection(),
    ).has_table(StripeSaaSBinding.__tablename__):
        return None
    for row in db.scalars(select(StripeSaaSBinding).where(
        StripeSaaSBinding.tenant_id == tenant_id, StripeSaaSBinding.livemode.is_(True),
    )):
        binding = _snapshot(row)
        if binding["subscriber_id"] != principal.get("user_id") or module_key not in binding["modules"]:
            continue
        evidence = subscription_status(db, row.id, tenant_id, principal, live=True)
        if evidence["status"] == "PAID" and module_key in evidence["modules"]:
            return {"subscription_id": row.id, "tenant_id": str(tenant_id), "module_key": module_key,
                    "expires_at": datetime.fromtimestamp(evidence["paid_until"], timezone.utc),
                    "basis": "STRIPE_PAID_PERIOD", "payment_verified": True, "has_access": True}
    return None


def scoped_subscription_outcomes(db, scope, *, live):
    """Aggregate exact verified paid periods without returning subscriber identities."""
    if not inspect(db.connection()).has_table(StripeSaaSBinding.__tablename__):
        return None
    stored_scope = StripeSaaSBinding.binding["scope"]
    candidates = db.scalars(select(StripeSaaSBinding).where(
        StripeSaaSBinding.livemode == live,
        *(stored_scope[key].as_string() == value for key, value in scope.items()),
    ).order_by(StripeSaaSBinding.id).limit(101)).all()
    if not candidates:
        return None
    _ready(db)
    current = int(_now().timestamp())
    observation = {
        "basis": "STRIPE_LIVE_PAID_PERIODS" if live else "STRIPE_TEST_PAID_PERIODS",
        "status": "OBSERVED", "verified_current_periods": 0, "verified_adjacent_renewals": 0,
        "scheduled_cancellations": 0, "held_agreements": 0,
        "recognized_revenue_minor": None, "available_cash_minor": None, "external_authority": False,
    }
    if len(candidates) > 100:
        return {**observation, "status": "REVIEW_REQUIRED"}
    for candidate in candidates:
        try:
            row, data, _ = _binding(db, candidate.id, live)
            if data["scope"] != scope:
                raise HTTPException(409, "Recurring outcome scope differs from its agreement")
            periods = db.scalars(select(StripePaidPeriod).where(
                StripePaidPeriod.binding_id == row.id,
                StripePaidPeriod.period_start <= current,
            ).order_by(StripePaidPeriod.period_start.desc()).limit(2)).all()
            evidence = [_period_value(row, period) for period in periods]
            if any(_reversed(db, row, period) for period in evidence):
                observation["held_agreements"] += 1
                continue
            if periods and periods[0].period_end > current:
                observation["verified_current_periods"] += 1
                observation["scheduled_cancellations"] += int(row.cancel_scheduled)
            if len(periods) == 2 and periods[1].period_end == periods[0].period_start:
                observation["verified_adjacent_renewals"] += 1
        except (HTTPException, KeyError, TypeError):
            observation["held_agreements"] += 1
    if observation["held_agreements"]:
        observation["status"] = "REVIEW_REQUIRED"
    return observation
