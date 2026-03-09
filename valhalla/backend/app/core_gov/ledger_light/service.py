from __future__ import annotations
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(date_str: str, kind: str, amount: float, description: str = "", category: str = "", account_id: str = "", ref: Dict[str, Any] = None) -> Dict[str, Any]:
    if not (date_str or "").strip():
        raise ValueError("date required (YYYY-MM-DD)")
    kind = (kind or "").strip().lower()
    if kind not in ("income","expense","transfer"):
        raise ValueError("kind must be income|expense|transfer")
    amt = float(amount or 0.0)
    if amt < 0:
        raise ValueError("amount must be >= 0")

    rec = {
        "id": "tx_" + uuid.uuid4().hex[:12],
        "date": date_str.strip(),
        "kind": kind,
        "amount": amt,
        "description": description or "",
        "category": category or "",
        "account_id": account_id or "",
        "ref": ref or {},
        "created_at": _utcnow_iso(),
    }
    tx = store.list_tx()
    tx.append(rec)
    store.save_tx(tx)
    return rec

def list_tx(kind: str = "", category: str = "", account_id: str = "", limit: int = 500) -> List[Dict[str, Any]]:
    tx = store.list_tx()
    if kind:
        tx = [t for t in tx if t.get("kind") == kind]
    if category:
        tx = [t for t in tx if t.get("category") == category]
    if account_id:
        tx = [t for t in tx if t.get("account_id") == account_id]
    tx.sort(key=lambda x: x.get("date",""), reverse=True)
    return tx[:max(1, min(5000, int(limit or 500)))]
