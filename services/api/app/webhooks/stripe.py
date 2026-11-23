"""Authenticate Stripe deliveries and acknowledge only durable journal receipts."""
from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.heimdall.authority import is_live
from app.providers.stripe_adapter import StripeAdapter
from app.services.stripe_finance import CHARGE_CORRECTION_EVENTS

router = APIRouter(prefix="/webhooks/stripe")

FINANCIAL_EVENTS = CHARGE_CORRECTION_EVENTS | {
    "payment_intent.succeeded",
    "payment_intent.payment_failed",
    "payout.failed",
    "payout.canceled",
    "invoice.paid",
    "invoice.payment_failed",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
    "checkout.session.async_payment_failed",
}


@router.post("")
async def stripe_webhook(req: Request):
    live = is_live()
    mode = os.getenv("VALHALLA_STRIPE_EVENT_MODE")
    if not live and mode is None:
        if req.headers.get("Stripe-Signature"):
            raise HTTPException(503, "STRIPE_FINANCIAL_EVENT_CONSUMER_NOT_VERIFIED")
        return {"status": "sandbox_ignored", "verified_financial_effect": False}

    raw = bytearray()
    async for chunk in req.stream():
        if len(raw) + len(chunk) > 1024 * 1024:
            raise HTTPException(413, "Stripe event exceeds supported size")
        raw.extend(chunk)
    body = bytes(raw)
    signature = req.headers.get("Stripe-Signature")
    if live:
        authenticated = StripeAdapter().validate_signature(body, signature)
    else:
        from app.providers.stripe_adapter import verify_stripe_signature

        secret = os.getenv("VALHALLA_STRIPE_TEST_WEBHOOK_SECRET")
        authenticated = (mode == "test" and secret != os.getenv("STRIPE_WEBHOOK_SECRET")
                         and verify_stripe_signature(body, signature, secret))
    if not authenticated:
        raise HTTPException(400, "invalid Stripe signature")
    try:
        payload = json.loads(body)
    except (ValueError, RecursionError):
        raise HTTPException(400, "invalid Stripe event payload") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("id"), str) or not isinstance(payload.get("type"), str):
        raise HTTPException(400, "missing Stripe event identity")
    if payload["type"] not in FINANCIAL_EVENTS:
        return {"status": "ignored", "verified_financial_effect": False}
    if mode != ("live" if live else "test"):
        raise HTTPException(503, "STRIPE_FINANCIAL_EVENT_CONSUMER_NOT_VERIFIED")

    from app.services.stripe_finance import persist_delivery

    return await run_in_threadpool(persist_delivery, payload, body, live)
