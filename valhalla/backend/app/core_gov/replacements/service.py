from __future__ import annotations

import uuid
from datetime import datetime, timezone, date, timedelta
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


def _calc_monthly_save(target_cost: float, months: int) -> float:
    m = max(1, int(months or 1))
    return round(float(target_cost or 0.0) / float(m), 2)


def create_replacement(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")
    try:
        cost = float(payload.get("target_cost"))
    except Exception:
        raise ValueError("target_cost must be a number")
    if cost < 0:
        raise ValueError("target_cost must be >= 0")

    months = int(payload.get("suggested_months") or 3)
    monthly_save = _calc_monthly_save(cost, months)

    now = _utcnow_iso()
    rid = "rp_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "name": name,
        "target_cost": float(cost),
        "currency": _norm(payload.get("currency") or "CAD") or "CAD",
        "priority": payload.get("priority") or "B",
        "status": payload.get("status") or "planned",
        "desired_by": _norm(payload.get("desired_by") or ""),
        "suggested_months": months,
        "monthly_save": monthly_save,
        "notes": payload.get("notes") or "",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_all()
    items.append(rec)
    store.save_all(items)

    # best-effort: reserve monthly via capital module (if it exists)
    try:
        from backend.app.deals import capital_store  # type: ignore
        capital_store.add_plan({
            "type": "replacement",
            "ref_id": rid,
            "monthly_amount": monthly_save,
            "currency": rec["currency"],
            "note": f"Replacement plan: {name}",
        })
    except Exception:
        pass

    return rec


def list_replacements(status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_all()
    if status:
        items = [x for x in items if x.get("status") == status]
    if priority:
        items = [x for x in items if x.get("priority") == priority]
    return items


def get_replacement(rid: str) -> Optional[Dict[str, Any]]:
    for x in store.list_all():
        if x["id"] == rid:
            return x
    return None


def patch_replacement(rid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_all()
    tgt = None
    for x in items:
        if x["id"] == rid:
            tgt = x
            break
    if not tgt:
        raise KeyError("replacement not found")

    for k in ["name","currency","priority","status","desired_by","notes"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","currency","desired_by") else patch.get(k)

    if "target_cost" in patch:
        tgt["target_cost"] = float(patch.get("target_cost") or 0.0)
    if "suggested_months" in patch:
        tgt["suggested_months"] = int(patch.get("suggested_months") or 3)

    # recompute monthly save if cost/months changed
    tgt["monthly_save"] = _calc_monthly_save(float(tgt.get("target_cost") or 0.0), int(tgt.get("suggested_months") or 3))

    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_all(items)
    return tgt


def plan(rid: str) -> Dict[str, Any]:
    r = get_replacement(rid)
    if not r:
        raise KeyError("replacement not found")

    steps = [
        "Confirm preferred specs/brand (optional).",
        f"Save {r.get('monthly_save')} per month for {r.get('suggested_months')} months.",
        "When fully funded, mark status=ready.",
        "Purchase during planned window, mark purchased, store receipt in Document Vault (when available).",
    ]

    # simple schedule suggestions
    today = date.today()
    horizon_days = int(r.get("suggested_months") or 3) * 30
    steps.append(f"Suggested purchase window: {(today + timedelta(days=horizon_days)).isoformat()} +/- 14 days")

    return {
        "id": r["id"],
        "name": r.get("name"),
        "target_cost": r.get("target_cost"),
        "suggested_months": r.get("suggested_months"),
        "monthly_save": r.get("monthly_save"),
        "schedule_suggestion": steps,
    }
