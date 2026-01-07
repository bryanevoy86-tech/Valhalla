from __future__ import annotations
from fastapi import APIRouter, HTTPException
from . import store
from .ledger_link import post_confirmation_to_ledger

router = APIRouter(prefix="/core/pay_confirm", tags=["core-pay-confirm"])

@router.post("")
def create(payment_id: str, paid_on: str, amount: float, currency: str = "CAD", method: str = "", ref: str = "", notes: str = ""):
    if not payment_id or not paid_on:
        raise HTTPException(status_code=400, detail="payment_id and paid_on required (YYYY-MM-DD)")
    return store.create(payment_id=payment_id, paid_on=paid_on, amount=amount, currency=currency, method=method, ref=ref, notes=notes)

@router.get("")
def list_items(payment_id: str = "", date_from: str = "", date_to: str = "", limit: int = 200):
    items = store.list_items()
    if payment_id:
        items = [x for x in items if x.get("payment_id") == payment_id]
    if date_from:
        items = [x for x in items if (x.get("paid_on") or "") >= date_from]
    if date_to:
        items = [x for x in items if (x.get("paid_on") or "") <= date_to]
    items.sort(key=lambda x: x.get("paid_on",""), reverse=True)
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.post("/{confirm_id}/post_to_ledger")
def post(confirm_id: str):
    items = store.list_items()
    it = next((x for x in items if x.get("id") == confirm_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    return post_confirmation_to_ledger(it)
