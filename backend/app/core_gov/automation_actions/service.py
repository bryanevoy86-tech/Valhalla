from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _hash_key(kind: str, ref: str) -> str:
    # stable dedupe key
    return f"{kind}:{ref}"


def _dedupe_recent(key: str, dedupe_days: int) -> bool:
    items = store.list_dedupe()
    cutoff = _utcnow() - timedelta(days=int(dedupe_days or 21))
    kept = []
    seen = False
    for x in items:
        dt = None
        try:
            dt = datetime.fromisoformat((x.get("created_at") or "").replace("Z", "+00:00"))
        except Exception:
            dt = None
        if dt and dt >= cutoff:
            kept.append(x)
            if x.get("key") == key:
                seen = True
    if len(kept) != len(items):
        store.save_dedupe(kept)
    return seen


def _mark_dedupe(key: str) -> None:
    items = store.list_dedupe()
    items.append({"id": "dd_" + uuid.uuid4().hex[:10], "key": key, "created_at": _utcnow_iso()})
    if len(items) > 800:
        items = items[-800:]
    store.save_dedupe(items)


def _safe(fn, warnings: List[str], label: str):
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{label} unavailable: {type(e).__name__}: {e}")
        return None


def _get_bill_events(lookahead_days: int, warnings: List[str]) -> List[Dict[str, Any]]:
    def _fn():
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        return cal.next_n_days_calendar(int(lookahead_days or 14))  # you may not have this; handled
    x = _safe(_fn, warnings, "budget_calendar")
    if not x:
        # try alternate shape from earlier pack (next_30_days_calendar)
        def _fn2():
            from backend.app.core_gov.budget import calendar as cal  # type: ignore
            return cal.next_30_days_calendar()
        x = _safe(_fn2, warnings, "budget_calendar_alt")
    return x.get("items", []) if isinstance(x, dict) else (x or [])


def _get_reorder_suggestions(warnings: List[str]) -> List[Dict[str, Any]]:
    def _fn():
        from backend.app.core_gov.inventory import reorder  # type: ignore
        r = reorder.suggest_reorders(max_items=25)
        return r.get("items", [])
    return _safe(_fn, warnings, "inventory_reorders") or []


def _create_followup(payload: Dict[str, Any], warnings: List[str]) -> Optional[Dict[str, Any]]:
    """
    Tries common followups interfaces.
    If none found, returns None with warning.
    """
    def _try():
        from backend.app.followups import store as fstore  # type: ignore

        # Try a few plausible function names
        for fn_name in ("create_followup", "add_followup", "enqueue_followup"):
            if hasattr(fstore, fn_name):
                fn = getattr(fstore, fn_name)
                return fn(payload)

        # Some implementations keep list + save
        if hasattr(fstore, "list_followups") and hasattr(fstore, "save_followups"):
            items = fstore.list_followups()
            rec = dict(payload)
            rec.setdefault("id", "fu_" + uuid.uuid4().hex[:12])
            items.append(rec)
            fstore.save_followups(items)
            return rec

        raise AttributeError("No compatible followups store function found")

    return _safe(_try, warnings, "followups_create")


def generate_followups(lookahead_days: int = 14, dedupe_days: int = 21, max_create: int = 30, mode: str = "execute", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    warnings: List[str] = []
    created = 0
    attempted = 0
    details: Dict[str, Any] = {"bill_followups": [], "reorder_followups": []}

    # In explore mode, we only report what WOULD be created
    dry = (mode == "explore")

    # Bills
    bills = _get_bill_events(lookahead_days, warnings)
    for b in bills or []:
        if created >= int(max_create or 30):
            break
        title = b.get("title") or b.get("name") or "Upcoming bill"
        due = b.get("date") or b.get("due_date") or ""
        ref = _norm(f"{title}:{due}")
        key = _hash_key("bill", ref)
        if _dedupe_recent(key, dedupe_days):
            continue

        attempted += 1
        fu = {
            "id": "fu_" + uuid.uuid4().hex[:12],
            "title": f"Pay bill: {title}",
            "status": "open",
            "due_date": due,
            "priority": "high",
            "source": "automation_actions",
            "meta": {"kind": "bill", "bill": b, **meta},
        }

        if dry:
            details["bill_followups"].append({"would_create": fu})
            _mark_dedupe(key)
            created += 1
            continue

        rec = _create_followup(fu, warnings)
        if rec:
            details["bill_followups"].append({"created": rec})
            _mark_dedupe(key)
            created += 1

    # Reorders
    reorders = _get_reorder_suggestions(warnings)
    for r in reorders or []:
        if created >= int(max_create or 30):
            break
        item_id = r.get("item_id") or ""
        ref = _norm(f"{item_id}:{r.get('reorder_qty')}:{r.get('location')}")
        key = _hash_key("reorder", ref)
        if _dedupe_recent(key, dedupe_days):
            continue

        attempted += 1
        due = (_utcnow() + timedelta(days=2)).date().isoformat()
        fu = {
            "id": "fu_" + uuid.uuid4().hex[:12],
            "title": f"Reorder: {r.get('name')}",
            "status": "open",
            "due_date": due,
            "priority": "normal" if r.get("priority") in ("normal","low") else "high",
            "source": "automation_actions",
            "meta": {"kind": "reorder", "reorder": r, **meta},
        }

        if dry:
            details["reorder_followups"].append({"would_create": fu})
            _mark_dedupe(key)
            created += 1
            continue

        rec = _create_followup(fu, warnings)
        if rec:
            details["reorder_followups"].append({"created": rec})
            _mark_dedupe(key)
            created += 1

    return {"created": created, "attempted": attempted, "warnings": warnings, "details": details}
