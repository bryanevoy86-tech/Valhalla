from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def mark_paid(
    obligation_id: str,
    paid_date: str,
    amount: float,
    method: str = "manual",           # manual|autopay|card|etransfer
    account_id: str = "",
    ledger_id: str = "",
    receipt_id: str = "",
    doc_id: str = "",
    confirmation: str = "",
    notes: str = "",
    meta: Dict[str, Any] = None,
) -> Dict[str, Any]:
    meta = meta or {}
    if not (obligation_id or "").strip():
        raise ValueError("obligation_id required")
    if not (paid_date or "").strip():
        raise ValueError("paid_date required (YYYY-MM-DD)")
    if float(amount or 0.0) < 0:
        raise ValueError("amount must be >= 0")

    rec = {
        "id": "pay_" + uuid.uuid4().hex[:12],
        "obligation_id": obligation_id.strip(),
        "paid_date": paid_date.strip(),
        "amount": float(amount or 0.0),
        "method": (method or "manual").strip(),
        "account_id": (account_id or "").strip(),
        "ledger_id": (ledger_id or "").strip(),
        "receipt_id": (receipt_id or "").strip(),
        "doc_id": (doc_id or "").strip(),
        "confirmation": confirmation or "",
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    
    # also push to ledger light (safe)
    try:
        from backend.app.core_gov.bill_payments.ledger_bridge import post_to_ledger  # type: ignore
        post_to_ledger(
            date=paid_date.strip(),
            amount=float(amount or 0.0),
            description=f"Bill paid: {obligation_id}",
            category="bills",
            account_id=account_id or "",
        )
    except Exception:
        pass
    
    return rec

def list_items(obligation_id: str = "", date_from: str = "", date_to: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if obligation_id:
        items = [x for x in items if x.get("obligation_id") == obligation_id]
    if date_from:
        items = [x for x in items if x.get("paid_date","") >= date_from]
    if date_to:
        items = [x for x in items if x.get("paid_date","") <= date_to]
    items.sort(key=lambda x: x.get("paid_date",""), reverse=True)
    return items[:10000]
