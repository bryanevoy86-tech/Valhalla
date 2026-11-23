"""Canonical provider event ingress and owner-controlled readback."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.heimdall.authority import is_live
from app.routers.auth_weweb import private_owner_response
from app.services.prime_business_execution import require_owner_mandate_key
from app.services.stripe_finance import configured_readback
from app.services.stripe_orders import OrderBindingIn, inspect_binding, register_binding
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
