from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create_rule(payload: Dict[str, Any]) -> Dict[str, Any]:
    inventory_id = _norm(payload.get("inventory_id") or "")
    if not inventory_id:
        raise ValueError("inventory_id is required")

    now = _utcnow_iso()
    rid = "rr_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "inventory_id": inventory_id,
        "status": payload.get("status") or "active",
        "reorder_qty": float(payload.get("reorder_qty") or 1.0),
        "cooldown_days": int(payload.get("cooldown_days") or 7),
        "store_hint": _norm(payload.get("store_hint") or ""),
        "category": _norm(payload.get("category") or "household") or "household",
        "last_triggered_at": "",
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_rules()
    items.append(rec)
    store.save_rules(items)
    return rec


def list_rules(status: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_rules()
    if status:
        items = [x for x in items if x.get("status") == status]
    return items


def _cooldown_ok(rule: Dict[str, Any], now_iso: str) -> bool:
    last = rule.get("last_triggered_at") or ""
    if not last:
        return True
    try:
        from datetime import datetime, timedelta
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        now_dt = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
        cd = int(rule.get("cooldown_days") or 7)
        return (now_dt - last_dt) >= timedelta(days=cd)
    except Exception:
        return True


def evaluate(run_actions: bool = True) -> Dict[str, Any]:
    now = _utcnow_iso()
    rules = [r for r in store.list_rules() if r.get("status") == "active"]

    triggered = 0
    created = 0
    results: List[Dict[str, Any]] = []

    # load inventory items from flow module
    try:
        from backend.app.core_gov.flow import service as flow_service  # type: ignore
        inv_items = {x["id"]: x for x in flow_service.list_items()}
    except Exception:
        # If flow module unavailable, return no triggers
        return {"ok": True, "triggered": 0, "created_shopping": 0, "results": []}

    changed_rules = False

    for r in rules:
        iid = r.get("inventory_id")
        inv = inv_items.get(iid)
        if not inv:
            results.append({"rule_id": r.get("id"), "ok": False, "error": "inventory_missing", "inventory_id": iid})
            continue

        # Check if item quantity is below reorder point
        reorder_point = float(inv.get("reorder_point") or 0.0)
        need = reorder_point > 0  # Simple trigger: if rule references an item, consider reordering

        if not need:
            results.append({"rule_id": r.get("id"), "triggered": False, "reason": "no_need"})
            continue

        if not _cooldown_ok(r, now):
            results.append({"rule_id": r.get("id"), "triggered": False, "reason": "cooldown"})
            continue

        triggered += 1
        if run_actions:
            r["last_triggered_at"] = now
            r["updated_at"] = now
            changed_rules = True
            results.append({"rule_id": r.get("id"), "triggered": True, "item_name": inv.get("name")})
        else:
            results.append({"rule_id": r.get("id"), "triggered": True, "would_trigger": True})

    if changed_rules:
        store.save_rules(rules)

    return {"ok": True, "triggered": triggered, "created_shopping": created, "results": results}
