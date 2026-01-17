from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict
from . import store
from .service import compute_next, schedule as sched
from .importers import import_all
from .autopay_verify import mark_enabled, mark_verified
from .reminders import push as push_reminders
from .export import export as export_payload

router = APIRouter(prefix="/core/payments", tags=["core-payments"])

@router.post("")
def create(
    name: str,
    amount: float,
    cadence: str = "monthly",
    currency: str = "CAD",
    due_day: int = 1,
    kind: str = "bill",
    payee: str = "",
    autopay_enabled: bool = False,
    autopay_verified: bool = False,
    account_id: str = "",
    notes: str = "",
):
    try:
        rec = store.create(
            name=name, amount=amount, cadence=cadence, currency=currency, due_day=due_day,
            kind=kind, payee=payee, autopay_enabled=autopay_enabled, autopay_verified=autopay_verified,
            account_id=account_id, notes=notes
        )
        try:
            from backend.app.core_gov.audit_log.store import append  # type: ignore
            append(area="payments", action="create", ref_id=rec.get("id",""), meta={"name": rec.get("name")})
        except Exception:
            pass
        return rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_items(status: str = "active", limit: int = 200):
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"items": items[:max(1, min(5000, int(limit or 200)))]}

@router.get("/{payment_id}")
def get(payment_id: str):
    items = store.list_items()
    it = next((x for x in items if x.get("id") == payment_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    return it

@router.patch("/{payment_id}")
def patch(payment_id: str, payload: Dict[str, Any] = Body(...)):
    items = store.list_items()
    it = next((x for x in items if x.get("id") == payment_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    p = payload or {}
    for k in ("name","kind","payee","amount","currency","cadence","due_day","next_due_override","autopay_enabled","autopay_verified","account_id","notes","status"):
        if k in p:
            it[k] = p[k]
    it["updated_at"] = store._utcnow()  # type: ignore
    store.save_items(items)
    try:
        from backend.app.core_gov.audit_log.store import append  # type: ignore
        append(area="payments", action="patch", ref_id=it.get("id",""), meta={"name": it.get("name")})
    except Exception:
        pass
    return it

@router.get("/{payment_id}/next_due")
def next_due_ep(payment_id: str):
    items = store.list_items()
    it = next((x for x in items if x.get("id") == payment_id), None)
    if not it:
        raise HTTPException(status_code=404, detail="not found")
    return {"payment_id": payment_id, "next_due": compute_next(it)}

@router.get("/schedule/upcoming")
def schedule_upcoming(days: int = 30, limit: int = 500):
    items = store.list_items()
    out = sched(items, days=days)
    return {"items": out[:max(1, min(5000, int(limit or 500)))]}

@router.post("/import_from_bills_and_subs")
def import_ep():
    return import_all()

@router.post("/{payment_id}/autopay_enabled")
def autopay_enabled_ep(payment_id: str, enabled: bool = True):
    out = mark_enabled(payment_id=payment_id, enabled=enabled)
    if not out.get("ok"):
        raise HTTPException(status_code=404, detail=out.get("error"))
    return out

@router.post("/{payment_id}/autopay_verified")
def autopay_verified_ep(payment_id: str, verified: bool = True, proof_note: str = ""):
    out = mark_verified(payment_id=payment_id, verified=verified, proof_note=proof_note)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out.get("error"))
    return out

@router.post("/push_reminders")
def push_reminders_ep(days_ahead: int = 5):
    return push_reminders(days_ahead=days_ahead)

@router.get("/export")
def export_ep(days: int = 90):
    return export_payload(days=days)
