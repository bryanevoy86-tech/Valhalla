from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_call(fn, warnings: List[str], label: str):
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{label} unavailable: {type(e).__name__}: {e}")
        return None


def _get_bill_calendar_next_30(warnings: List[str]):
    def _fn():
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        return cal.next_30_days_calendar()
    return _safe_call(_fn, warnings, "bill_calendar")


def _get_obligations_status(warnings: List[str]):
    def _fn():
        from backend.app.core_gov.obligations import service as oblig  # type: ignore
        return oblig.obligations_status(buffer_multiplier=1.25)
    return _safe_call(_fn, warnings, "obligations_status")


def _get_followups_due(warnings: List[str]):
    def _fn():
        from backend.app.followups import store as fstore  # type: ignore
        items = fstore.list_followups()  # expect list[dict]
        # light filter: due_date present and status open-ish
        out = []
        for x in items or []:
            if x.get("status") in ("done", "closed", "archived"):
                continue
            if x.get("due_date"):
                out.append(x)
        out.sort(key=lambda r: r.get("due_date",""))
        return out[:25]
    return _safe_call(_fn, warnings, "followups")


def _get_budget_month_snapshot(month: str, warnings: List[str]):
    if not month:
        return None

    def _fn():
        from backend.app.core_gov.budget import service as bsvc  # type: ignore
        return bsvc.month_plan_view(month)
    return _safe_call(_fn, warnings, "budget_month_plan")


def _get_reorder_candidates_stub(warnings: List[str]):
    """
    v1 stub: returns empty until pantry/inventory is built.
    """
    return {
        "items": [],
        "note": "Inventory/Pantry module not installed yet. Add Pantry/Inventory packs to enable auto-reorder candidates."
    }


def run_house_ops(run_type: str = "manual", month: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    warnings: List[str] = []

    bill_calendar = _get_bill_calendar_next_30(warnings)
    obligations = _get_obligations_status(warnings)
    followups = _get_followups_due(warnings)
    budget = _get_budget_month_snapshot(month, warnings) if month else None
    reorders = _get_reorder_candidates_stub(warnings)

    results = {
        "bill_calendar_next_30": bill_calendar,
        "obligations_status": obligations,
        "followups_due": followups,
        "budget_month_snapshot": budget,
        "reorder_candidates": reorders,
    }

    rid = "ar_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "run_type": run_type or "manual",
        "created_at": _utcnow_iso(),
        "meta": meta,
        "warnings": warnings,
        "results": results,
    }

    items = store.list_runs()
    items.append(rec)
    # keep last 200
    if len(items) > 200:
        items = items[-200:]
    store.save_runs(items)
    return rec


def list_runs(limit: int = 25) -> List[Dict[str, Any]]:
    items = store.list_runs()
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[: int(limit or 25)]


def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_runs():
        if x.get("id") == run_id:
            return x
    return None
