"""One-time paid product access guarded by an exact buyer and capture."""
import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, field_validator
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.stripe_finance import StripeFinancialEvent, StripeOrderBinding
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event, _json
from app.services.stripe_finance import _event_receipt, read_captured_charge, stripe_id, stripe_readback_client
from app.services.stripe_orders import _require_configured_mode, _require_tables, _reversal_pending, _snapshot
from app.services.specialist_triggers import outcome_scope_key
from app.users.models import AccountSettings, UserProfile

GRANT = "STRIPE_ONE_TIME_DELIVERY_AUTHORIZED"
ACCEPTANCE = "STRIPE_BUYER_ACKNOWLEDGED_DELIVERY"
OFFERED = "STRIPE_PRODUCT_DELIVERY_OFFERED"
REVOKED = "STRIPE_PRODUCT_DELIVERY_REVOKED"


class FulfillmentIn(StrictModel):
    tenant_id: UUID
    subscriber_id: int = Field(strict=True, gt=0)
    stripe_customer_id: str
    signed_event_id: str
    commercial_rights_reference: str = Field(min_length=10, max_length=180)
    attestation: str = Field(pattern=r"^OWNER_AUTHORIZES_EXACT_PAID_PRODUCT_DELIVERY$")

    @field_validator("stripe_customer_id", "signed_event_id")
    @classmethod
    def native_reference(cls, value, info):
        prefix = "cus" if info.field_name == "stripe_customer_id" else "evt"
        if not stripe_id(value, prefix):
            raise ValueError("A native Stripe reference is required")
        return value


class RevokeDeliveryIn(StrictModel):
    reason_reference: str = Field(min_length=8, max_length=180)


class DeliveryAcceptanceIn(StrictModel):
    grant_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _key(order_id):
    return f"STRIPE-DELIVERY-{order_id}"


def _scope_active(scope, *, live):
    if live and (os.getenv("VALHALLA_STRIPE_DELIVERY_ENABLED") != "1"
                 or os.getenv("VALHALLA_STRIPE_DELIVERY_SCOPE") != outcome_scope_key(scope)):
        raise HTTPException(503, "Paid product delivery is not authorized for this scope")


def _locked_order(db, order_id, live):
    account = _require_configured_mode(live)
    _require_tables(db)
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        raise HTTPException(503, "Stripe delivery evidence journal unavailable")
    order = db.get(StripeOrderBinding, order_id, with_for_update=True)
    if order is None or order.livemode is not live:
        raise HTTPException(404, "Paid product order unavailable")
    binding = _snapshot(order)
    if binding["stripe_account_id"] != account:
        raise HTTPException(409, "Paid product order belongs to another processor account")
    return order, binding


def _read_record(db, key, kind, scope):
    row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=key))
    if row is None:
        return None
    raw = _json(row.payload_json, {})
    data = raw.get("value") if isinstance(raw, dict) else None
    if (not isinstance(data, dict) or row.event_type != kind or row.legacy_instance_id != scope["legacy_instance_id"]
            or data.get("scope") != scope or raw.get("sha256") != artifact_digest(kind, key, data)):
        raise HTTPException(409, "Paid delivery journal failed integrity")
    return {**data, "sha256": raw["sha256"]}


def _write_record(db, key, kind, value):
    digest = artifact_digest(kind, key, value)
    _event(db, event_id=key, legacy_instance_id=value["scope"]["legacy_instance_id"], event_type=kind,
           message="Scoped paid product delivery evidence", payload={"value": value, "sha256": digest})
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concurrent delivery evidence exists; retry the exact request") from None
    return {**value, "sha256": digest}


def _buyer(db, subject_id):
    return db.scalar(select(UserProfile).join(AccountSettings, AccountSettings.user_id == UserProfile.user_id)
                     .where(UserProfile.user_id == subject_id, AccountSettings.account_locked.is_(False)))


def _check_product(db, binding):
    from app.routers.foundry_checkout import _listing

    receipt, artifact, price, scope = _listing(db, binding["action_id"])
    if (receipt["sha256"], str(artifact.id), artifact.product_id, artifact.sha256, price, scope) != (
        binding["listing_sha256"], binding["product_asset_id"], binding["product_id"], binding["product_sha256"],
        binding["amount_minor"], binding["scope"],
    ):
        raise HTTPException(409, "Paid delivery product differs from approved listing")
    return artifact


def delivery_buyer_reference(order_id, tenant_id, subscriber_id):
    return artifact_digest("stripe_delivery_buyer", str(order_id), {
        "tenant_id": str(tenant_id), "subscriber_id": subscriber_id,
    })


def _check_capture(db, order, binding, event_id, customer, tenant_id, subscriber_id):
    event = db.get(StripeFinancialEvent, event_id)
    if event is None or event.livemode is not order.livemode:
        raise HTTPException(409, "Signed capture unavailable")
    _event_receipt(event, True)
    snapshot = event.snapshot
    if (snapshot.get("kind"), snapshot.get("payment_intent_id"), snapshot.get("stripe_customer_id"),
            snapshot.get("merchant_order_id"), snapshot.get("amount_minor"), snapshot.get("currency")) != (
        "payment_intent.succeeded", order.payment_intent_id, customer, str(order.id),
        binding["amount_minor"], binding["currency"],
    ):
        raise HTTPException(409, "Signed capture differs from exact paid buyer and order")
    if (snapshot.get("tenant_id"), snapshot.get("buyer_ref")) != (
        str(tenant_id), delivery_buyer_reference(order.id, tenant_id, subscriber_id),
    ):
        raise HTTPException(409, "Signed capture differs from the subscriber and tenant binding")
    if _reversal_pending(db, order, snapshot.get("charge_id")):
        raise HTTPException(409, "Paid delivery is held for refund or dispute review")
    return event


def authorize_delivery(db, order_id, request: FulfillmentIn, *, client, account_id, live):
    order, binding = _locked_order(db, order_id, live)
    scope = binding["scope"]
    _scope_active(scope, live=live)
    if account_id != binding["stripe_account_id"] or _buyer(db, request.subscriber_id) is None:
        raise HTTPException(409, "Exact Stripe account and active subscriber required")
    _check_product(db, binding)
    event = _check_capture(db, order, binding, request.signed_event_id, request.stripe_customer_id,
                           request.tenant_id, request.subscriber_id)
    read_captured_charge(client, account_id, event.snapshot)
    value = {**request.model_dump(mode="json"), "scope": scope, "order_sha256": order.binding_sha256,
             "order_id": str(order_id), "capture_sha256": event.snapshot_sha256, "product_id": binding["product_id"],
             "basis": "PAID_ONE_TIME_PRODUCT" if live else "SYNTHETIC_DELIVERY_REHEARSAL"}
    key = _key(order_id)
    prior = _read_record(db, key, GRANT, scope)
    if prior is not None:
        if {k: v for k, v in prior.items() if k != "sha256"} != value:
            raise HTTPException(409, "This order already has a different delivery authorization")
        return prior
    return _write_record(db, key, GRANT, value)


def configured_delivery(db, order_id, request, *, live):
    with stripe_readback_client(live=live) as (client, account_id):
        return authorize_delivery(db, order_id, request, client=client, account_id=account_id, live=live)


def delivery_access(db, tenant_id, order_id, principal, *, live):
    order, binding = _locked_order(db, order_id, live)
    scope = binding["scope"]
    grant = _read_record(db, _key(order_id), GRANT, scope)
    if (type(principal.get("user_id")) is not int or grant is None
            or (grant.get("tenant_id"), grant.get("subscriber_id")) != (str(tenant_id), principal["user_id"])):
        raise HTTPException(404, "Paid product delivery unavailable")
    profile = _buyer(db, principal["user_id"])
    if profile is None or profile.email != principal.get("sub"):
        raise HTTPException(401, "Subscriber identity unavailable")
    _scope_active(scope, live=live)
    if _read_record(db, f"STRIPE-DELIVERY-REVOKE-{order_id}", REVOKED, scope):
        raise HTTPException(409, "Paid delivery authorization has been revoked")
    event = _check_capture(db, order, binding, grant["signed_event_id"], grant["stripe_customer_id"],
                           tenant_id, principal["user_id"])
    if (grant.get("order_id"), grant.get("order_sha256"), grant.get("capture_sha256"), grant.get("basis")) != (
        str(order_id), order.binding_sha256, event.snapshot_sha256,
        "PAID_ONE_TIME_PRODUCT" if live else "SYNTHETIC_DELIVERY_REHEARSAL",
    ):
        raise HTTPException(409, "Paid delivery grant evidence changed")
    artifact = _check_product(db, binding)
    if live:
        with stripe_readback_client(live=live) as (client, account_id):
            read_captured_charge(client, account_id, event.snapshot)
    return artifact, grant


def acknowledge_delivery(db, tenant_id, order_id, principal, request, *, live):
    _, grant = delivery_access(db, tenant_id, order_id, principal, live=live)
    if request.grant_sha256 != grant["sha256"]:
        raise HTTPException(409, "Delivery acknowledgment does not match the authorized product")
    scope = grant["scope"]
    if live:
        offered = _read_record(db, f"STRIPE-DELIVERY-OFFER-{order_id}", OFFERED, scope)
        if offered is None or offered.get("grant_sha256") != grant["sha256"]:
            raise HTTPException(409, "Product must be offered to this buyer before acknowledgment")
    key = f"STRIPE-DELIVERY-ACK-{order_id}"
    prior = _read_record(db, key, ACCEPTANCE, scope)
    value = {"scope": scope, "order_id": str(order_id), "tenant_id": str(tenant_id),
             "grant_sha256": grant["sha256"], "subscriber_id": principal["user_id"], "basis": grant["basis"],
             "buyer_acknowledged": True, "recognized_revenue_minor": None, "available_cash_minor": None}
    if prior is not None:
        if {k: v for k, v in prior.items() if k not in {"sha256", "acknowledged_on"}} != value:
            raise HTTPException(409, "Delivery acknowledgment differs from the recorded acceptance")
        return prior
    return _write_record(db, key, ACCEPTANCE, {
        **value, "acknowledged_on": datetime.now(timezone.utc).date().isoformat(),
    })



def record_delivery_offer(db, order_id, grant):
    scope = grant["scope"]
    key = f"STRIPE-DELIVERY-OFFER-{order_id}"
    data = {"scope": scope, "order_id": str(order_id), "grant_sha256": grant["sha256"],
            "basis": grant["basis"], "offered_for_download": True}
    prior = _read_record(db, key, OFFERED, scope)
    if prior is not None:
        if {k: v for k, v in prior.items() if k != "sha256"} != data:
            raise HTTPException(409, "Delivery offer differs from the original entitlement")
        return prior
    return _write_record(db, key, OFFERED, data)


def revoke_delivery(db, order_id, request, *, live):
    _, binding = _locked_order(db, order_id, live)
    scope = binding["scope"]
    grant = _read_record(db, _key(order_id), GRANT, scope)
    if grant is None:
        raise HTTPException(404, "Paid product delivery unavailable")
    key = f"STRIPE-DELIVERY-REVOKE-{order_id}"
    prior = _read_record(db, key, REVOKED, scope)
    if prior is not None:
        if prior.get("reason_reference") != request.reason_reference:
            raise HTTPException(409, "Revocation reference differs from recorded evidence")
        return prior
    return _write_record(db, key, REVOKED, {
        "scope": scope, "order_id": str(order_id), "grant_sha256": grant["sha256"],
        "reason_reference": request.reason_reference, "basis": grant["basis"], "revoked": True,
    })
