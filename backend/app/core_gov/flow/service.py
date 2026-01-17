from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(tags: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tags or []:
        t2 = _norm(t)
        if t2 and t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def _get_item(item_id: str) -> Optional[Dict[str, Any]]:
    for it in store.list_items():
        if it["id"] == item_id:
            return it
    return None


def create_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    now = _utcnow_iso()
    iid = "si_" + uuid.uuid4().hex[:12]
    rec = {
        "id": iid,
        "name": name,
        "item_type": payload.get("item_type") or "household",
        "status": payload.get("status") or "active",
        "preferred_brand": _norm(payload.get("preferred_brand") or ""),
        "preferred_size": _norm(payload.get("preferred_size") or ""),
        "est_unit_cost": float(payload.get("est_unit_cost") or 0.0),
        "reorder_point": float(payload.get("reorder_point") or 1.0),
        "target_level": float(payload.get("target_level") or 3.0),
        "cadence_days": int(payload.get("cadence_days") or 14),
        "store_pref": _norm(payload.get("store_pref") or ""),
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items(status: Optional[str] = None, item_type: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if item_type:
        items = [x for x in items if x.get("item_type") == item_type]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    return items


def patch_item(item_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for it in items:
        if it["id"] == item_id:
            tgt = it
            break
    if not tgt:
        raise KeyError("item not found")

    for k in ["name","item_type","status","preferred_brand","preferred_size","store_pref"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","preferred_brand","preferred_size","store_pref") else patch.get(k)
    for k in ["est_unit_cost","reorder_point","target_level"]:
        if k in patch:
            tgt[k] = float(patch.get(k) or 0.0)
    if "cadence_days" in patch:
        tgt["cadence_days"] = int(patch.get("cadence_days") or 14)

    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt


def upsert_inventory(payload: Dict[str, Any]) -> Dict[str, Any]:
    item_id = _norm(payload.get("item_id") or "")
    if not item_id:
        raise ValueError("item_id is required")
    it = _get_item(item_id)
    if not it:
        raise KeyError("item not found")

    level = float(payload.get("current_level") or 0.0)
    urgency = payload.get("urgency") or "medium"
    note = payload.get("note") or ""

    inv = store.list_inventory()
    now = _utcnow_iso()

    tgt = None
    for x in inv:
        if x.get("item_id") == item_id:
            tgt = x
            break

    rec = {"item_id": item_id, "current_level": level, "urgency": urgency, "note": note, "updated_at": now}
    if tgt:
        tgt.update(rec)
    else:
        inv.append(rec)
    store.save_inventory(inv)

    # auto: if below reorder_point -> add to shopping
    try:
        if level <= float(it.get("reorder_point") or 1.0) and it.get("status") == "active":
            needed = max(0.0, float(it.get("target_level") or 3.0) - level)
            if needed > 0:
                add_to_shopping(item_id=item_id, qty=needed, urgency=urgency, note="auto_reorder")
    except Exception:
        pass

    return rec


def get_inventory(item_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_inventory():
        if x.get("item_id") == item_id:
            return x
    return None


def _cone_safe_can_spend(urgency: str) -> bool:
    # If obligations module exists and not covered, only allow HIGH/CRITICAL.
    try:
        from backend.app.core_gov.obligations import service as oblig_service  # type: ignore
        st = oblig_service.obligations_status(buffer_multiplier=1.25)
        covered = st.get("covered")
        if covered is False and urgency not in ("high", "critical"):
            return False
    except Exception:
        pass
    return True


def add_to_shopping(item_id: str, qty: float = 1.0, urgency: str = "medium", note: str = "") -> Dict[str, Any]:
    it = _get_item(item_id)
    if not it:
        raise KeyError("item not found")
    if it.get("status") != "active":
        raise ValueError("item is not active")

    # cone-safe gate
    if not _cone_safe_can_spend(urgency):
        # queue as followup instead of adding to shopping
        try:
            from backend.app.deals import followups_store  # type: ignore
            followups_store.create_followup({
                "title": f"DEFERRED BUY (Obligations not covered): {it.get('name')}",
                "due_date": datetime.now().date().isoformat(),
                "priority": "B",
                "status": "open",
                "meta": {"item_id": item_id, "qty": qty, "urgency": urgency, "note": note},
            })
        except Exception:
            pass
        return {
            "queued": True,
            "reason": "obligations_not_covered",
            "item_id": item_id,
            "qty": qty,
            "urgency": urgency,
            "note": note,
        }

    now = _utcnow_iso()
    sid = "sh_" + uuid.uuid4().hex[:12]
    est = float(it.get("est_unit_cost") or 0.0) * float(qty or 1.0)

    rec = {
        "id": sid,
        "item_id": item_id,
        "name": it.get("name") or "",
        "qty": float(qty or 1.0),
        "est_cost": round(est, 2),
        "urgency": urgency or "medium",
        "status": "open",
        "note": note or "",
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_shopping()
    items.append(rec)
    store.save_shopping(items)

    # best-effort: reserve money via capital module
    try:
        from backend.app.deals import capital_store  # type: ignore
        capital_store.add_reservation({
            "type": "shopping",
            "ref_id": sid,
            "amount": rec["est_cost"],
            "currency": "CAD",
            "note": f"Shopping reserve: {rec['name']}",
        })
    except Exception:
        pass

    return rec


def list_shopping(status: Optional[str] = None, urgency: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_shopping()
    if status:
        items = [x for x in items if x.get("status") == status]
    if urgency:
        items = [x for x in items if x.get("urgency") == urgency]
    return items


def mark_shopping(item_id: str, status: str) -> Dict[str, Any]:
    items = store.list_shopping()
    tgt = None
    for x in items:
        if x["id"] == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("shopping item not found")

    if status not in ("open", "done", "canceled"):
        raise ValueError("status must be open/done/canceled")

    tgt["status"] = status
    tgt["updated_at"] = _utcnow_iso()
    store.save_shopping(items)
    return tgt
