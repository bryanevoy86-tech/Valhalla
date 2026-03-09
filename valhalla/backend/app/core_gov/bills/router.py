from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from . import store
from .due import upcoming
from .reminders import push as push_reminders
from .autopay import checklist, checklist_for_all
from .nlp_intake import create_from_candidate
from .pay_log import mark_paid, missed

router = APIRouter(prefix="/core/bills", tags=["core-bills"])

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.post("")
def create(name: str, amount: float, cadence: str = "monthly", due_day: int = 1, due_months: int = 1, payee: str = "", account_hint: str = "", autopay: bool = False, notes: str = ""):
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    rec = {
        "id": store.new_id(),
        "name": name,
        "amount": float(amount or 0.0),
        "cadence": (cadence or "monthly").lower(),  # monthly|weekly|yearly|every_n_months
        "due_day": int(due_day or 1),               # day of month for monthly/every_n_months
        "due_months": int(due_months or 1),         # for every_n_months (e.g. water bill every 3)
        "payee": payee or "",
        "account_hint": account_hint or "",
        "autopay": bool(autopay),
        "notes": notes or "",
        "status": "active",
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    bills = store.list_bills()
    bills.append(rec)
    store.save_bills(bills)
    return rec

@router.get("")
def list_bills(status: str = "active", limit: int = 200):
    bills = store.list_bills()
    if status:
        bills = [b for b in bills if b.get("status") == status]
    bills.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"bills": bills[:max(1, min(5000, int(limit or 200)))]}

@router.patch("/{bill_id}")
def patch(bill_id: str, payload: Dict[str, Any] = Body(...)):
    bills = store.list_bills()
    b = next((x for x in bills if x.get("id") == bill_id), None)
    if not b:
        raise HTTPException(status_code=404, detail="not found")
    p = payload or {}
    for k in ("name","amount","cadence","due_day","due_months","payee","account_hint","autopay","notes","status"):
        if k in p:
            b[k] = p[k]
    b["updated_at"] = _utcnow()
    store.save_bills(bills)
    return b

@router.get("/upcoming")
def upcoming_ep(limit: int = 50):
    return upcoming(limit=limit)

@router.post("/push_reminders")
def push_reminders_ep(days_ahead: int = 7):
    return push_reminders(days_ahead=days_ahead)

@router.get("/{bill_id}/autopay_checklist")
def autopay_checklist(bill_id: str):
    bills = store.list_bills()
    b = next((x for x in bills if x.get("id") == bill_id), None)
    if not b:
        raise HTTPException(status_code=404, detail="not found")
    return checklist(b)

@router.get("/autopay_checklists")
def autopay_checklists():
    return checklist_for_all(store.list_bills())

@router.post("/{bill_id}/paid")
def paid(bill_id: str, paid_on: str = "", amount: float = 0.0, notes: str = ""):
    try:
        return mark_paid(bill_id=bill_id, paid_on=paid_on, amount=amount, notes=notes)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/missed")
def missed_ep():
    return missed()

@router.post("/from_candidate")
def from_candidate(payload: Dict[str, Any] = Body(...)):
    return create_from_candidate(candidate=(payload or {}).get("candidate") or {})
