from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_monthly_report(month: str, include_details: bool = False, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    warnings: List[str] = []

    # Plan (obligations + shopping)
    plan_full = None
    try:
        from backend.app.core_gov.budget import full_plan  # type: ignore
        plan_full = full_plan.month_plan_full(month)
        if plan_full.get("warnings"):
            warnings += plan_full.get("warnings")
    except Exception as e:
        warnings.append(f"budget_full_plan unavailable: {type(e).__name__}: {e}")
        plan_full = None

    # Actuals
    actuals = None
    try:
        from backend.app.core_gov.budget import actuals as act  # type: ignore
        actuals = act.month_actuals(month)
        if actuals.get("warnings"):
            warnings += actuals.get("warnings")
    except Exception as e:
        warnings.append(f"budget_actuals unavailable: {type(e).__name__}: {e}")
        actuals = None

    report = {
        "month": month,
        "plan": plan_full or {},
        "actuals": actuals or {},
        "variance": {},
        "notes": "Plan vs Actuals variance is informational. Improve by setting receipt categories + shopping est_unit_cost.",
    }

    try:
        plan_total = float((plan_full or {}).get("grand_total") or 0.0)
        actual_total = float((actuals or {}).get("grand_total") or 0.0)
        report["variance"] = {
            "plan_total": plan_total,
            "actual_total": actual_total,
            "delta_actual_minus_plan": float(actual_total - plan_total),
        }
    except Exception:
        report["variance"] = {}

    if not include_details:
        # strip heavy lists
        if "plan" in report and isinstance(report["plan"], dict):
            report["plan"].pop("shopping_items", None)
            report["plan"].pop("obligations", None)

    rec = {
        "id": "mr_" + uuid.uuid4().hex[:12],
        "month": month,
        "created_at": _utcnow_iso(),
        "meta": meta,
        "warnings": warnings,
        "report": report,
    }

    items = store.list_monthly()
    items.append(rec)
    if len(items) > 120:
        items = items[-120:]
    store.save_monthly(items)
    return rec


def list_monthly(limit: int = 25) -> List[Dict[str, Any]]:
    items = store.list_monthly()
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[: int(limit or 25)]


def get_monthly(report_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_monthly():
        if x.get("id") == report_id:
            return x
    return None
