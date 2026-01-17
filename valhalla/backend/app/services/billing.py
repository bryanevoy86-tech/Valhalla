import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import stripe
from backend.app.models.billing import SeatCounter, Subscription, UsageMeter
from backend.app.models.org import Org
from sqlalchemy.orm import Session

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICES = {
    "starter": os.getenv("STRIPE_PRICE_STARTER"),
    "pro": os.getenv("STRIPE_PRICE_PRO"),
    "metered": os.getenv("STRIPE_PRICE_METERED"),
}


def ensure_customer(org: Org) -> str:
    if getattr(org, "stripe_customer_id", None):
        return org.stripe_customer_id
    customer = stripe.Customer.create(
        name=org.name,
        metadata={"org_id": org.id},
    )
    org.stripe_customer_id = customer["id"]
    return org.stripe_customer_id


def create_checkout_session(
    org: Org, plan_key: str, seats: int = 1, success_url: str = "", cancel_url: str = ""
) -> str:
    price = PRICES.get(plan_key)
    if not price:
        raise ValueError("Unknown plan key")
    customer = ensure_customer(org)
    line_items = [
        {
            "price": price,
            "quantity": max(1, seats),
        }
    ]
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer,
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        automatic_tax={"enabled": True},
    )
    return session["url"]


def create_portal_session(customer_id: str, return_url: str) -> str:
    s = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
    return s["url"]


def upsert_subscription(db: Session, org_id: int, sub_obj: Dict[str, Any]):
    sub_id = sub_obj["id"]
    status = sub_obj["status"]
    items = [
        {
            "price": it["price"]["id"],
            "qty": it["quantity"],
            "billing_scheme": it["price"]["billing_scheme"],
        }
        for it in sub_obj["items"]["data"]
    ]
    row = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
    plan_key = None
    for it in items:
        if it["price"] == PRICES.get("starter"):
            plan_key = "starter"
        if it["price"] == PRICES.get("pro"):
            plan_key = "pro"
    if not row:
        row = Subscription(
            org_id=org_id,
            stripe_subscription_id=sub_id,
            status=status,
            plan_key=plan_key,
            items=items,
            current_period_end=datetime.fromtimestamp(
                sub_obj["current_period_end"], tz=timezone.utc
            ),
            cancel_at_period_end=sub_obj.get("cancel_at_period_end", False),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    else:
        row.status = status
        row.items = items
        row.plan_key = plan_key
        row.current_period_end = datetime.fromtimestamp(
            sub_obj["current_period_end"], tz=timezone.utc
        )
        row.cancel_at_period_end = sub_obj.get("cancel_at_period_end", False)
        db.commit()
    return row


def set_seats(db: Session, org_id: int, seats: int):
    sc = db.query(SeatCounter).filter(SeatCounter.org_id == org_id).first()
    if not sc:
        sc = SeatCounter(org_id=org_id, seats=max(1, seats))
        db.add(sc)
    else:
        sc.seats = max(1, seats)
    db.commit()
    return sc.seats


def bump_usage(db: Session, org_id: int, key: str, qty: int = 1):
    row = db.query(UsageMeter).filter(UsageMeter.org_id == org_id, UsageMeter.key == key).first()
    if not row:
        row = UsageMeter(org_id=org_id, key=key, qty=qty)
        db.add(row)
    else:
        row.qty += qty
    db.commit()


def post_metered_usage(subscription_item_id: str, quantity: int, timestamp: int | None = None):
    if not PRICES.get("metered"):
        return
    stripe.UsageRecord.create(
        quantity=quantity,
        timestamp=timestamp or int(time.time()),
        action="increment",
        subscription_item=subscription_item_id,
    )


def find_subscription_item_for_price(sub: Dict[str, Any], price_id: str) -> Optional[str]:
    for it in sub["items"]["data"]:
        if it["price"]["id"] == price_id:
            return it["id"]
    return None
