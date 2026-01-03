from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(
    kind: str,                 # income|expense|transfer
    date: str,                 # YYYY-MM-DD
    amount: float,
    description: str = "",
    category: str = "",
    merchant: str = "",
    account_id: str = "",
    obligation_id: str = "",
    receipt_id: str = "",
    tags: List[str] = None,
    meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    tags = tags or []
    meta = meta or {}
    k = (kind or "").strip().lower()
    if k not in ("income","expense","transfer"):
        raise ValueError("kind must be income|expense|transfer")
    if not (date or "").strip():
        raise ValueError("date required (YYYY-MM-DD)")
    amt = float(amount or 0.0)
    if amt < 0:
        raise ValueError("amount must be >= 0")

    rec = {
        "id": "led_" + uuid.uuid4().hex[:12],
        "kind": k,
        "date": date.strip(),
        "amount": amt,
        "description": description or "",
        "category": category or "",
        "merchant": merchant or "",
        "account_id": (account_id or "").strip(),
        "obligation_id": (obligation_id or "").strip(),
        "receipt_id": (receipt_id or "").strip(),
        "tags": tags,
        "meta": meta,
        "created_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(kind: str = "", category: str = "", account_id: str = "", q: str = "", date_from: str = "", date_to: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if kind:
        kk = kind.strip().lower()
        items = [x for x in items if x.get("kind") == kk]
    if category:
        items = [x for x in items if x.get("category") == category]
    if account_id:
        items = [x for x in items if x.get("account_id") == account_id]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("description","").lower()) or qq in (x.get("merchant","").lower())]
    if date_from:
        items = [x for x in items if (x.get("date","") >= date_from)]
    if date_to:
        items = [x for x in items if (x.get("date","") <= date_to)]
    items.sort(key=lambda x: (x.get("date",""), x.get("created_at","")), reverse=True)
    return items[:10000]

def summary(date_from: str = "", date_to: str = "") -> Dict[str, Any]:
    items = list_items(date_from=date_from, date_to=date_to)
    inc = sum(float(x.get("amount") or 0.0) for x in items if x.get("kind") == "income")
    exp = sum(float(x.get("amount") or 0.0) for x in items if x.get("kind") == "expense")
    return {"date_from": date_from, "date_to": date_to, "income": float(inc), "expense": float(exp), "net": float(inc - exp), "count": len(items)}
