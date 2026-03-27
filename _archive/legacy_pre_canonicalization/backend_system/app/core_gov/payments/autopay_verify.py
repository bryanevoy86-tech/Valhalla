from __future__ import annotations
from typing import Any, Dict
from . import store

def mark_enabled(payment_id: str, enabled: bool = True) -> Dict[str, Any]:
    items = store.list_items()
    it = next((x for x in items if x.get("id") == payment_id), None)
    if not it:
        return {"ok": False, "error": "not found"}
    it["autopay_enabled"] = bool(enabled)
    it["autopay_verified"] = False if not enabled else bool(it.get("autopay_verified"))
    it["updated_at"] = store._utcnow()  # type: ignore
    store.save_items(items)
    return {"ok": True, "payment": it}

def mark_verified(payment_id: str, verified: bool = True, proof_note: str = "") -> Dict[str, Any]:
    items = store.list_items()
    it = next((x for x in items if x.get("id") == payment_id), None)
    if not it:
        return {"ok": False, "error": "not found"}
    if not bool(it.get("autopay_enabled")) and verified:
        return {"ok": False, "error": "cannot verify when autopay_enabled is false"}
    it["autopay_verified"] = bool(verified)
    if proof_note:
        it["notes"] = (it.get("notes") or "") + f"\n[autopay-proof] {proof_note}"
    it["updated_at"] = store._utcnow()  # type: ignore
    store.save_items(items)
    return {"ok": True, "payment": it}
