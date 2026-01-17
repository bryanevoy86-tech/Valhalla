from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_rule(name: str, contains: str, category: str, tags_add: List[str] = None, confidence: float = 0.8, status: str = "active") -> Dict[str, Any]:
    name = (name or "").strip()
    contains = (contains or "").strip().lower()
    category = (category or "").strip()
    if not name:
        raise ValueError("name required")
    if not contains:
        raise ValueError("contains required")
    if not category:
        raise ValueError("category required")

    rec = {
        "id": "bcr_" + uuid.uuid4().hex[:12],
        "name": name,
        "status": status,
        "contains": contains,
        "category": category,
        "confidence": float(confidence or 0.8),
        "tags_add": tags_add or [],
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_rules()
    items.append(rec)
    store.save_rules(items)
    return rec


def list_rules(status: str = "") -> List[Dict[str, Any]]:
    items = store.list_rules()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: float(x.get("confidence") or 0.0), reverse=True)
    return items


def categorize_txn(txn: Dict[str, Any]) -> Dict[str, Any]:
    desc = (txn.get("description") or "").lower()
    rules = list_rules(status="active")
    for r in rules:
        if r.get("contains") and r["contains"] in desc:
            return {
                "category": r.get("category",""),
                "confidence": float(r.get("confidence") or 0.0),
                "matched_rule_id": r.get("id",""),
                "matched_rule_name": r.get("name",""),
                "tags_add": r.get("tags_add") or [],
            }
    return {"category": "", "confidence": 0.0, "matched_rule_id": "", "matched_rule_name": "", "tags_add": []}


def apply_to_bank_txn(bank_txn_id: str, create_receipt: bool = False) -> Dict[str, Any]:
    warnings: List[str] = []
    res = {"category": "", "confidence": 0.0, "matched_rule_id": "", "matched_rule_name": "", "tags_add": []}
    try:
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        txn = bsvc.get_one(bank_txn_id)
        if not txn:
            return {"bank_txn_id": bank_txn_id, "warnings": ["bank txn not found"], "result": {}}
        res = categorize_txn(txn)
        if res.get("category"):
            new_tags = list(set((txn.get("tags") or []) + (res.get("tags_add") or []) + [f"cat:{res['category']}"]))
            bsvc.patch(bank_txn_id, {"meta": {**(txn.get("meta") or {}), "bank_categorizer": res}, "tags": new_tags})
        else:
            warnings.append("no rule match")
    except Exception as e:
        return {"bank_txn_id": bank_txn_id, "warnings": [f"bank unavailable: {type(e).__name__}: {e}"], "result": {}}

    receipt = {}
    if create_receipt and res.get("category"):
        try:
            from backend.app.core_gov.receipts import service as rsvc  # type: ignore
            receipt = rsvc.create({
                "vendor": txn.get("description","")[:80] or "Bank txn",
                "date": txn.get("date",""),
                "total": float(txn.get("amount") or 0.0),
                "currency": txn.get("currency","CAD"),
                "source": "bank",
                "status": "categorized",
                "category": res.get("category",""),
                "tags": (res.get("tags_add") or []) + ["from_bank_txn"],
                "notes": "Auto-created from bank txn. Verify vendor/date/amount.",
                "meta": {"bank_txn_id": bank_txn_id, "bank_categorizer": res},
            })
        except Exception as e:
            warnings.append(f"receipt create failed: {type(e).__name__}: {e}")

    return {"bank_txn_id": bank_txn_id, "warnings": warnings, "result": res, "receipt": receipt}
