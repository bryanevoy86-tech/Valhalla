import os
from typing import Any, Dict

import stripe
from backend.app.deps.tenant import get_db, org_membership
from backend.app.models.org import Org
from backend.app.services.billing import (
    PRICES,
    bump_usage,
    create_checkout_session,
    create_portal_session,
    find_subscription_item_for_price,
    set_seats,
    upsert_subscription,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
def start_checkout(
    payload: Dict[str, Any],
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
):
    org: Org = db.query(Org).filter(Org.id == ctx["org_id"]).first()
    if not org:
        raise HTTPException(status_code=404, detail="Org not found")
    url = create_checkout_session(
        org=org,
        plan_key=payload.get("plan", "starter"),
        seats=int(payload.get("seats", 1)),
        success_url=os.getenv("STRIPE_SUCCESS_URL", "https://example.com"),
        cancel_url=os.getenv("STRIPE_CANCEL_URL", "https://example.com"),
    )
    return {"url": url}


@router.post("/portal")
def portal(
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
):
    org: Org = db.query(Org).filter(Org.id == ctx["org_id"]).first()
    if not org or not org.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Stripe customer not set")
    url = create_portal_session(
        org.stripe_customer_id, os.getenv("STRIPE_PORTAL_RETURN_URL", "https://example.com")
    )
    return {"url": url}


@router.post("/seats")
def update_seats(
    payload: Dict[str, Any],
    ctx=Depends(org_membership(["owner", "admin"])),
    db: Session = Depends(get_db),
):
    seats = max(1, int(payload.get("seats", 1)))
    new_val = set_seats(db, ctx["org_id"], seats)
    return {"seats": new_val}


@router.post("/usage")
def add_usage(
    payload: Dict[str, Any], ctx=Depends(org_membership()), db: Session = Depends(get_db)
):
    key = payload.get("key", "ai_calls")
    qty = int(payload.get("qty", 1))
    bump_usage(db, ctx["org_id"], key, qty)
    return {"ok": True}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    wh_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=wh_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    etype = event["type"]
    data = event["data"]["object"]

    org_id = None
    try:
        if data.get("customer"):
            cust = stripe.Customer.retrieve(data["customer"])
            org_id = (
                int(cust["metadata"].get("org_id"))
                if cust and cust.get("metadata") and cust["metadata"].get("org_id")
                else None
            )
    except Exception:
        pass

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        if not org_id:
            pass
        upsert_subscription(db, org_id=org_id or 0, sub_obj=data)
        if PRICES.get("metered"):
            try:
                sub = stripe.Subscription.retrieve(data["id"], expand=["items.data.price"])
                item_id = find_subscription_item_for_price(sub, PRICES["metered"])
                if item_id:
                    pass
            except Exception:
                pass
    elif etype == "invoice.paid" or etype == "invoice.payment_failed":
        pass

    return {"ok": True}
