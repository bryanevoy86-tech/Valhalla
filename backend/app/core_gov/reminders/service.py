from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> date:
    return date.today()


def _norm(s: str) -> str:
    return (s or "").strip()


def _existing_refs(items: List[Dict[str, Any]]) -> set:
    out = set()
    for x in items:
        r = _norm(x.get("ref") or "")
        if r:
            out.add(r)
    return out


def create(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = _norm(payload.get("title") or "")
    due_date = _norm(payload.get("due_date") or "")
    if not title:
        raise ValueError("title is required")
    if not due_date:
        raise ValueError("due_date is required (YYYY-MM-DD)")

    now = _utcnow_iso()
    rid = "rm_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "title": title,
        "due_date": due_date,
        "status": payload.get("status") or "active",
        "priority": payload.get("priority") or "normal",
        "source": payload.get("source") or "manual",
        "ref": _norm(payload.get("ref") or ""),
        "notes": payload.get("notes") or "",
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items(status: str = "", source: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if source:
        items = [x for x in items if x.get("source") == source]
    items.sort(key=lambda x: (x.get("due_date",""), x.get("priority","normal")))
    return items


def patch(item_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("reminder not found")

    for k in ["title","due_date","status","priority","source","ref","notes"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("title","due_date","ref") else (patch.get(k) or "")
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt


def _safe(fn, warnings: List[str], label: str):
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{label} unavailable: {type(e).__name__}: {e}")
        return None


def generate_from_budget(lookahead_days: int = 30, lead_days: int = 3, max_create: int = 50) -> Dict[str, Any]:
    warnings: List[str] = []
    created: List[Dict[str, Any]] = []

    # events from budget calendar
    def _get():
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        return cal.next_n_days_calendar(int(lookahead_days or 30))
    cal_out = _safe(_get, warnings, "budget_calendar")
    events = (cal_out or {}).get("items", []) if isinstance(cal_out, dict) else (cal_out or [])

    items = store.list_items()
    refs = _existing_refs(items)

    for ev in events:
        if len(created) >= int(max_create or 50):
            break
        if ev.get("type") != "obligation":
            continue
        due = (ev.get("date") or "").strip()
        if not due:
            continue

        # reminder due lead_days before bill
        try:
            y, m, d = [int(x) for x in due.split("-")]
            due_dt = date(y, m, d)
            remind_dt = due_dt - timedelta(days=int(lead_days or 3))
            remind_date = remind_dt.isoformat()
        except Exception:
            remind_date = due  # fallback

        ref = f"budget_obligation:{ev.get('obligation_id')}:{remind_date}"
        if ref in refs:
            continue

        rec = {
            "title": f"Upcoming bill: {ev.get('title')}",
            "due_date": remind_date,
            "status": "active",
            "priority": "high" if not ev.get("autopay_enabled") else "normal",
            "source": "budget",
            "ref": ref,
            "notes": "Verify funds + payment method. If manual, pay before due date.",
            "meta": {"event": ev},
        }
        created.append(create(rec))
        refs.add(ref)

    return {"created": len(created), "warnings": warnings, "items": created}


def generate_from_shopping(default_lead_days: int = 2, max_create: int = 50) -> Dict[str, Any]:
    warnings: List[str] = []
    created: List[Dict[str, Any]] = []

    def _get():
        from backend.app.core_gov.shopping import service as ssvc  # type: ignore
        return ssvc.list_items(status="open")
    shop = _safe(_get, warnings, "shopping")
    shop_items = shop or []

    items = store.list_items()
    refs = _existing_refs(items)

    for it in shop_items:
        if len(created) >= int(max_create or 50):
            break

        desired_by = (it.get("desired_by") or "").strip()
        if desired_by:
            due_date = desired_by
        else:
            due_date = (_today() + timedelta(days=int(default_lead_days or 2))).isoformat()

        ref = f"shopping:{it.get('id')}:{due_date}"
        if ref in refs:
            continue

        pr = it.get("priority") or "normal"
        rec = {
            "title": f"Buy: {it.get('name')}",
            "due_date": due_date,
            "status": "active",
            "priority": pr if pr in ("low","normal","high","critical") else "normal",
            "source": "shopping",
            "ref": ref,
            "notes": f"Preferred store: {it.get('preferred_store','')}".strip(),
            "meta": {"shopping_item_id": it.get("id")},
        }
        created.append(create(rec))
        refs.add(ref)

    return {"created": len(created), "warnings": warnings, "items": created}
