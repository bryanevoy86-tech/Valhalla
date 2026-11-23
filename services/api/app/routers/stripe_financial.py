"""Canonical provider event ingress and owner-controlled readback."""
import os
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.heimdall.authority import is_live
from app.routers.auth_weweb import get_current_user, private_owner_response
from app.services.prime_business_execution import require_owner_mandate_key
from app.services.stripe_finance import configured_readback
from app.services.stripe_fulfillment import (
    DeliveryAcceptanceIn, FulfillmentIn, RevokeDeliveryIn, acknowledge_delivery, configured_delivery, delivery_access,
    record_delivery_offer, revoke_delivery,
)
from app.services.stripe_bank_booking import BankBatchIn, configured_bank_batch
from app.services.stripe_orders import OrderBindingIn, inspect_binding, register_binding
from app.services.stripe_revenue_release import DeliveryReleaseIn, recognize_delivery
from app.services.stripe_refund_correction import RefundCorrectionIn, configured_refund_correction
from app.services.stripe_recurring import (
    InvoiceProofIn, RecurringBindingIn, apply_paid_invoice, bind_recurring, recurring_clients, schedule_cancellation,
    start_checkout, subscription_status, verify_period_payout, verify_period_processor_balance,
)
from app.webhooks.stripe import router as stripe_webhooks

router = APIRouter()
router.include_router(stripe_webhooks)
owner_keys = [Depends(require_prime_control_key), Depends(require_owner_mandate_key)]


@router.post("/api/governance/floor/stripe-events/{event_id}/processor-readback",
             dependencies=owner_keys)
def readback(event_id: str, db: Session = Depends(get_db)):
    return private_owner_response(configured_readback(db, event_id, live=is_live()))



@router.post("/api/governance/floor/stripe-orders", status_code=201, dependencies=owner_keys)
def bind_checkout_order(payload: OrderBindingIn, db: Session = Depends(get_db)):
    return private_owner_response(register_binding(db, payload, live=is_live()), status_code=201)


@router.get("/api/governance/floor/stripe-orders/{order_id}", dependencies=owner_keys)
def inspect_checkout_order(order_id: UUID, db: Session = Depends(get_db)):
    return private_owner_response(inspect_binding(db, order_id, live=is_live()))


@router.post("/api/governance/floor/stripe-orders/{order_id}/payout-readback/{payout_id}", dependencies=owner_keys)
def read_checkout_payout(order_id: UUID, payout_id: str, db: Session = Depends(get_db)):
    from app.services.stripe_payout_evidence import configured_payout_readback

    return private_owner_response(configured_payout_readback(db, order_id, payout_id, live=is_live()))



@router.post("/api/governance/floor/stripe-bank-batches/reconcile", dependencies=owner_keys)
def confirm_bank_batch(payload: BankBatchIn, db: Session = Depends(get_db)):
    return private_owner_response(configured_bank_batch(db, payload, live=is_live()))



@router.post("/api/governance/floor/stripe-orders/{order_id}/delivery", dependencies=owner_keys)
def authorize_paid_delivery(order_id: UUID, payload: FulfillmentIn, db: Session = Depends(get_db)):
    grant = configured_delivery(db, order_id, payload, live=is_live())
    return private_owner_response({"order_id": grant["order_id"], "tenant_id": grant["tenant_id"],
                                   "product_id": grant["product_id"], "grant_sha256": grant["sha256"],
                                   "basis": grant["basis"], "available_cash_minor": None})


@router.get("/api/weweb/paid-products/{tenant_id}/{order_id}")
def paid_product(tenant_id: UUID, order_id: UUID, principal: dict = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    live = is_live()
    artifact, grant = delivery_access(db, tenant_id, order_id, principal, live=live)
    if not live:
        return private_owner_response({"order_id": str(order_id), "tenant_id": str(tenant_id),
                                       "basis": grant["basis"], "product_id": grant["product_id"],
                                       "grant_sha256": grant["sha256"], "download_enabled": False})
    record_delivery_offer(db, order_id, grant)
    return Response(content=artifact.data, media_type="application/octet-stream", headers={
        "Content-Disposition": f'attachment; filename="{artifact.id}.bin"', "Cache-Control": "no-store",
        "Vary": "Authorization", "X-Content-Type-Options": "nosniff", "X-Delivery-Grant": grant["sha256"],
    })


@router.post("/api/weweb/paid-products/{tenant_id}/{order_id}/acknowledge")
def acknowledge_paid_product(tenant_id: UUID, order_id: UUID, payload: DeliveryAcceptanceIn,
                             principal: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return private_owner_response(acknowledge_delivery(db, tenant_id, order_id, principal, payload, live=is_live()))



@router.post("/api/governance/floor/stripe-orders/{order_id}/delivery/revoke", dependencies=owner_keys)
def revoke_paid_delivery(order_id: UUID, payload: RevokeDeliveryIn, db: Session = Depends(get_db)):
    receipt = revoke_delivery(db, order_id, payload, live=is_live())
    return private_owner_response({"order_id": str(order_id), "revoked": receipt["revoked"],
                                   "revocation_sha256": receipt["sha256"]})



@router.post("/api/governance/floor/stripe-orders/{order_id}/delivery/release-liability", dependencies=owner_keys)
def release_paid_delivery_liability(order_id: UUID, payload: DeliveryReleaseIn, db: Session = Depends(get_db)):
    return private_owner_response(recognize_delivery(db, order_id, payload, live=is_live()))



@router.post("/api/governance/floor/stripe-orders/{order_id}/refund-correction", dependencies=owner_keys)
def correct_stripe_refund(order_id: UUID, payload: RefundCorrectionIn, db: Session = Depends(get_db)):
    return private_owner_response(configured_refund_correction(db, order_id, payload, live=is_live()))



@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/bind", status_code=201, dependencies=owner_keys)
def commission_recurring_binding(local_id: int, payload: RecurringBindingIn, db: Session = Depends(get_db)):
    return private_owner_response(bind_recurring(db, local_id, payload, live=is_live()), status_code=201)


@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/paid-period", dependencies=owner_keys)
def verify_paid_period(local_id: int, payload: InvoiceProofIn, db: Session = Depends(get_db)):
    live = is_live()
    with recurring_clients(live=live) as (reader, _):
        return private_owner_response(apply_paid_invoice(db, local_id, payload, live=live, client=reader))


@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/paid-period/{invoice_id}/processor-balance",
             dependencies=owner_keys)
def verify_recurring_processor_balance(local_id: int, invoice_id: str, payload: InvoiceProofIn,
                                       db: Session = Depends(get_db)):
    live = is_live()
    with recurring_clients(live=live) as (reader, _):
        return private_owner_response(verify_period_processor_balance(
            db, local_id, invoice_id, payload.event_id, live=live, client=reader,
        ))


@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/paid-period/{invoice_id}/payout/{payout_id}",
             dependencies=owner_keys)
def verify_recurring_payout(local_id: int, invoice_id: str, payout_id: str, db: Session = Depends(get_db)):
    live = is_live()
    with recurring_clients(live=live) as (reader, _):
        return private_owner_response(verify_period_payout(
            db, local_id, invoice_id, payout_id, live=live, client=reader,
            destination_id=os.getenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID"),
        ))


@router.post("/api/weweb/stripe-subscriptions/{tenant_id}/{local_id}/checkout")
def subscriber_checkout(tenant_id: UUID, local_id: int, principal: dict = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    live = is_live()
    with recurring_clients(live=live, write=True) as (reader, writer):
        return private_owner_response(start_checkout(
            db, local_id, tenant_id, principal, live=live, reader=reader, writer=writer,
            success_url=os.getenv("VALHALLA_STRIPE_RECURRING_SUCCESS_URL"),
            cancel_url=os.getenv("VALHALLA_STRIPE_RECURRING_CANCEL_URL"),
        ))


@router.get("/api/weweb/stripe-subscriptions/{tenant_id}/{local_id}")
def subscriber_recurring_status(tenant_id: UUID, local_id: int, principal: dict = Depends(get_current_user),
                                db: Session = Depends(get_db)):
    return private_owner_response(subscription_status(db, local_id, tenant_id, principal, live=is_live()))


@router.post("/api/weweb/stripe-subscriptions/{tenant_id}/{local_id}/cancel-at-period-end")
def subscriber_end_recurring(tenant_id: UUID, local_id: int, principal: dict = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    live = is_live()
    with recurring_clients(live=live, write=True) as (reader, writer):
        return private_owner_response(schedule_cancellation(
            db, local_id, tenant_id, principal, live=live, reader=reader, writer=writer,
        ))
