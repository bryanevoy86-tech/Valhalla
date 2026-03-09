from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create_rule(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    pattern = _norm(payload.get("pattern") or "").lower()
    category = _norm(payload.get("category") or "")
    if not name:
        raise ValueError("name is required")
    if not pattern:
        raise ValueError("pattern is required")
    if not category:
        raise ValueError("category is required")

    now = _utcnow_iso()
    rid = "cr_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "name": name,
        "status": payload.get("status") or "active",
        "rule_type": payload.get("rule_type") or "vendor_contains",
        "pattern": pattern,
        "category": category,
        "confidence": float(payload.get("confidence") or 0.7),
        "tags_add": payload.get("tags_add") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_rules()
    items.append(rec)
    store.save_rules(items)
    return rec


def list_rules(status: str = "") -> List[Dict[str, Any]]:
    items = store.list_rules()
    if status:
        items = [x for x in items if x.get("status") == status]
    # highest confidence first
    items.sort(key=lambda x: float(x.get("confidence") or 0.0), reverse=True)
    return items


def _match_rule(rule: Dict[str, Any], receipt: Dict[str, Any]) -> bool:
    rtype = rule.get("rule_type")
    pat = (rule.get("pattern") or "").lower()
    if not pat:
        return False

    if rtype == "vendor_contains":
        return pat in (receipt.get("vendor","").lower())
    if rtype == "tag_contains":
        tags = [str(t).lower() for t in (receipt.get("tags") or [])]
        return any(pat in t for t in tags)
    if rtype == "notes_contains":
        return pat in (receipt.get("notes","").lower())
    return False


def categorize_receipt(receipt_id: str, apply: bool = True, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    warnings: List[str] = []

    try:
        from backend.app.core_gov.receipts import service as rsvc  # type: ignore
        receipt = rsvc.get_one(receipt_id)
    except Exception as e:
        return {
            "receipt_id": receipt_id,
            "category": "",
            "confidence": 0.0,
            "matched_rule_id": "",
            "matched_rule_name": "",
            "tags_add": [],
            "warnings": [f"receipts unavailable: {type(e).__name__}: {e}"],
            "receipt_snapshot": {},
        }

    if not receipt:
        return {
            "receipt_id": receipt_id,
            "category": "",
            "confidence": 0.0,
            "matched_rule_id": "",
            "matched_rule_name": "",
            "tags_add": [],
            "warnings": ["receipt not found"],
            "receipt_snapshot": {},
        }

    rules = [r for r in list_rules(status="active")]
    match = None
    for r in rules:
        if _match_rule(r, receipt):
            match = r
            break

    if not match:
        return {
            "receipt_id": receipt_id,
            "category": "",
            "confidence": 0.0,
            "matched_rule_id": "",
            "matched_rule_name": "",
            "tags_add": [],
            "warnings": ["no rule match"],
            "receipt_snapshot": receipt,
        }

    cat = match.get("category") or ""
    conf = float(match.get("confidence") or 0.0)
    tags_add = match.get("tags_add") or []

    if apply:
        try:
            from backend.app.core_gov.receipts import service as rsvc  # type: ignore
            new_tags = list(set((receipt.get("tags") or []) + tags_add))
            rsvc.patch(receipt_id, {"category": cat, "status": "categorized", "tags": new_tags, "meta": {**(receipt.get("meta") or {}), "categorizer": {"rule_id": match.get("id"), **meta}}})
        except Exception as e:
            warnings.append(f"apply failed: {type(e).__name__}: {e}")

    return {
        "receipt_id": receipt_id,
        "category": cat,
        "confidence": conf,
        "matched_rule_id": match.get("id",""),
        "matched_rule_name": match.get("name",""),
        "tags_add": tags_add,
        "warnings": warnings,
        "receipt_snapshot": receipt,
    }
