"""Stripe webhook ingress: authenticate before parsing or acknowledging business outcomes.

No payment or refund is booked here until a real idempotent financial-ledger
consumer is wired in. A 503 causes Stripe to retry rather than losing a paid
event while returning fictional "payment_recorded" success.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

from app.heimdall.authority import is_live
from app.providers.stripe_adapter import StripeAdapter

router = APIRouter(prefix="/webhooks/stripe")

FINANCIAL_EVENTS = {
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "charge.refunded",
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "checkout.session.async_payment_failed",
}


@router.post("")
async def stripe_webhook(req: Request):
    if not is_live():
        # Shadow/sandbox must have NO financial side effects.
        return {"status": "sandbox_ignored", "verified_financial_effect": False}

    raw_body = await req.body()
    if not StripeAdapter().validate_signature(raw_body, req.headers.get("Stripe-Signature")):
        raise HTTPException(status_code=400, detail="invalid Stripe signature")

    try:
        payload = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="invalid Stripe event payload") from None

    if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
        raise HTTPException(status_code=400, detail="missing Stripe event identity")

    kind = payload.get("type")
    if kind not in FINANCIAL_EVENTS:
        return {"status": "ignored", "verified_financial_effect": False}

    # Not safe to acknowledge a payment before the event is persistently
    # deduplicated, reconciled, and applied to a ledger with provider evidence.
    # Codex must connect the canonical payment/receipt pipeline first.
    raise HTTPException(
        status_code=503,
        detail="STRIPE_FINANCIAL_EVENT_CONSUMER_NOT_VERIFIED",
    )
