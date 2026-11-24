"""Canonical provider event ingress and owner-controlled readback."""
from datetime import datetime, timezone
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
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
from app.services.stripe_bank_reversal import BankReversalIn, configured_bank_reversal
from app.services.stripe_bank_booking import BankBatchIn, configured_bank_batch, scoped_bank_blockers
from app.services.stripe_orders import (
    OrderBindingIn, SandboxPaymentPlanIn, inspect_binding, register_binding, sandbox_payment_plan,
)
from app.services.stripe_revenue_release import DeliveryReleaseIn, recognize_delivery
from app.schemas.market_intelligence import MarketScope
from app.services.treasury_cash_position import CashPositionRequest, reconcile_cash_position, verify_cash_close, verify_journal_head
from app.services.stripe_dispute_correction import ChargebackIn, configured_chargeback, configured_subscription_chargeback
from app.services.stripe_refund_correction import (
    RefundCorrectionIn, configured_refund_correction, configured_subscription_refund,
)
from app.services.stripe_recurring import (
    InvoiceProofIn, RecurringBindingIn, apply_paid_invoice, bind_recurring, recurring_clients, schedule_cancellation,
    start_checkout, subscriber_recurring_list, subscription_status, verify_period_payout, verify_period_processor_balance,
)
from app.services.stripe_subscription_delivery import (
    SubscriptionAckIn, SubscriptionReleaseIn, acknowledge_service, recognize_service, subscriber_service_history,
)
from app.webhooks.stripe import router as stripe_webhooks

router = APIRouter()
router.include_router(stripe_webhooks)
owner_keys = [Depends(require_prime_control_key), Depends(require_owner_mandate_key)]


@router.post("/api/governance/floor/stripe-events/{event_id}/processor-readback",
             dependencies=owner_keys)
def readback(event_id: str, db: Session = Depends(get_db)):
    return private_owner_response(configured_readback(db, event_id, live=is_live()))



@router.post("/api/governance/floor/stripe-orders/sandbox-payment-plan", dependencies=owner_keys)
def prepare_sandbox_payment(payload: SandboxPaymentPlanIn, db: Session = Depends(get_db)):
    return private_owner_response(sandbox_payment_plan(db, payload, live=is_live()))


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



@router.post("/api/governance/floor/stripe-bank-batches/balance-observation", dependencies=owner_keys)
def observe_payout_bank_balance(scope: MarketScope, db: Session = Depends(get_db)):
    from app.banking.plaid_transactions import configured_bank_balance
    from app.services.specialist_triggers import outcome_scope_key

    requested = scope.model_dump()
    if os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE") != outcome_scope_key(requested):
        raise HTTPException(409, "Bank observation requires the exact approved receiving scope")
    live = is_live()
    blockers = scoped_bank_blockers(db, requested, live=live)
    observation = configured_bank_balance(live=live, stripe_destination=os.getenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID"))
    return private_owner_response({"scope": requested, **observation,
                                   "spendable_cash_blockers": sorted(blockers | {"INDEPENDENT_LIABILITIES_AND_RESERVES_REQUIRED"})})


@router.post("/api/governance/floor/stripe-bank-batches/cash-close", dependencies=owner_keys)
def reconcile_scoped_cash_close(request: CashPositionRequest, db: Session = Depends(get_db)):
    from app.banking.plaid_transactions import configured_bank_balance
    from sqlalchemy import inspect
    from app.models.completion_registry import LegacyOrchestrationEvent
    from app.models.stripe_finance import StripeFinancialEvent
    from app.routers.economic_control import context, require_schema
    from app.services.economic_control import require_no_containment
    from app.services.prime_business_execution import _emergency_stop_active
    from app.services.specialist_triggers import outcome_scope_key

    payload = request.signed_close
    scope = payload.scope.model_dump()
    if os.getenv("VALHALLA_STRIPE_BANK_BOOKING_SCOPE") != outcome_scope_key(scope):
        raise HTTPException(409, "Cash close requires the exact approved receiving scope")
    live = is_live()
    verify_cash_close(db, payload, live=live, now=datetime.now(timezone.utc))
    bank = configured_bank_balance(live=live, stripe_destination=os.getenv("VALHALLA_STRIPE_PAYOUT_DESTINATION_ID"))
    verify_journal_head(db, payload)
    blockers = scoped_bank_blockers(db, scope, live=live)
    if _emergency_stop_active(db):
        blockers.add("EMERGENCY_STOP")
    if live:
        schema = inspect(db.connection())
        if any(not schema.has_table(model.__tablename__) for model in (LegacyOrchestrationEvent, StripeFinancialEvent)):
            raise HTTPException(503, "Current settlement and correction journal unavailable")
        require_schema(db)
        operation, state, _ = context(db, payload.scope, lock=False)
        if operation.currency != "CAD" or state.mandate is None or state.mandate.review_by < datetime.now(timezone.utc).date():
            blockers.add("CURRENT_CAD_CAPITAL_MANDATE_REQUIRED")
        else:
            operating = sum(item.amount_minor for item in payload.protections if item.category == "operating_reserve")
            if operating < state.mandate.min_operating_reserve:
                blockers.add("OPERATING_RESERVE_BELOW_APPROVED_FLOOR")
        try:
            require_no_containment(db, scope)
        except HTTPException as error:
            if error.status_code != 409:
                raise
            blockers.add("CAPITAL_CONTAINMENT")
    return private_owner_response(reconcile_cash_position(
        payload, bank, blockers, live=live, preferences=request.allocation_preferences,
    ))


@router.post("/api/governance/floor/stripe-bank-batches/reversal", dependencies=owner_keys)
def reconcile_bank_reversal(payload: BankReversalIn, db: Session = Depends(get_db)):
    return private_owner_response(configured_bank_reversal(db, payload, live=is_live()))


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
    extension = {"application/pdf": "pdf", "application/zip": "zip", "text/plain": "txt"}.get(
        artifact.media_type, "bin",
    )
    return Response(content=artifact.data, media_type="application/octet-stream", headers={
        "Content-Disposition": f'attachment; filename="{artifact.id}.{extension}"', "Cache-Control": "no-store",
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



@router.post("/api/governance/floor/stripe-orders/{order_id}/chargeback-correction", dependencies=owner_keys)
def reconcile_chargeback(order_id: UUID, payload: ChargebackIn, db: Session = Depends(get_db)):
    return private_owner_response(configured_chargeback(db, order_id, payload, live=is_live()))


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


@router.get("/api/weweb/stripe-subscriptions/{tenant_id}")
def subscriber_recurring_accounts(tenant_id: UUID, before: int | None = Query(None, gt=0),
                                  principal: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return private_owner_response(subscriber_recurring_list(db, tenant_id, principal, live=is_live(), before=before))


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


@router.get("/api/weweb/stripe-subscriptions/{tenant_id}/{local_id}/service-history")
def paid_service_history(tenant_id: UUID, local_id: int, principal: dict = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    return private_owner_response(subscriber_service_history(db, tenant_id, local_id, principal, live=is_live()))


@router.post("/api/weweb/stripe-subscriptions/{tenant_id}/{local_id}/paid-period/{invoice_id}/acknowledge")
def acknowledge_paid_service(tenant_id: UUID, local_id: int, invoice_id: str, payload: SubscriptionAckIn,
                             principal: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return private_owner_response(acknowledge_service(db, tenant_id, local_id, invoice_id, payload, principal, live=is_live()))


@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/paid-period/{invoice_id}/release-liability",
             dependencies=owner_keys)
def release_paid_service(local_id: int, invoice_id: str, payload: SubscriptionReleaseIn, db: Session = Depends(get_db)):
    return private_owner_response(recognize_service(db, local_id, invoice_id, payload, live=is_live()))


@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/paid-period/{invoice_id}/chargeback-correction",
             dependencies=owner_keys)
def reconcile_recurring_chargeback(local_id: int, invoice_id: str, payload: ChargebackIn,
                                   db: Session = Depends(get_db)):
    return private_owner_response(configured_subscription_chargeback(db, local_id, invoice_id, payload, live=is_live()))


@router.post("/api/governance/floor/stripe-subscriptions/{local_id}/paid-period/{invoice_id}/refund-correction",
             dependencies=owner_keys)
def reconcile_recurring_refund(local_id: int, invoice_id: str, payload: RefundCorrectionIn,
                               db: Session = Depends(get_db)):
    return private_owner_response(configured_subscription_refund(db, local_id, invoice_id, payload, live=is_live()))
