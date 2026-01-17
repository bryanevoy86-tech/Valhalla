from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import date, datetime


def _safe(fn, warnings: List[str], label: str) -> Optional[Any]:
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{label} unavailable: {type(e).__name__}: {e}")
        return None


def month_plan_full(month: str = "") -> Dict[str, Any]:
    """
    Full month plan combining obligations + open shopping estimates.
    month format: "2026-01" (YYYY-MM)
    """
    if not month:
        today = date.today()
        month = f"{today.year}-{today.month:02d}"

    warnings: List[str] = []
    plan: Dict[str, Any] = {}

    # 1. Get obligations (from month_plan_view)
    def _obligations():
        from backend.app.core_gov.budget import service as bsvc  # type: ignore
        return bsvc.month_plan_view(month)

    oblig_data = _safe(_obligations, warnings, "budget_obligations") or {}
    if oblig_data:
        plan["obligations"] = oblig_data.get("items", [])
        plan["obligations_total"] = oblig_data.get("total", 0.0)
    else:
        plan["obligations"] = []
        plan["obligations_total"] = 0.0

    # 2. Get open shopping items with est_unit_cost
    def _shopping():
        from backend.app.core_gov.shopping import service as ssvc  # type: ignore
        return ssvc.list_items(status="open")

    shopping_list = _safe(_shopping, warnings, "shopping") or []

    # Filter to items with desired_by in target month
    shopping_for_month = []
    for it in shopping_list:
        desired = (it.get("desired_by") or "").strip()
        if desired and desired.startswith(month):
            shopping_for_month.append(it)

    # Calculate shopping total (qty * est_unit_cost)
    shopping_total = 0.0
    for it in shopping_for_month:
        qty = float(it.get("qty") or 1)
        price = float(it.get("est_unit_cost") or 0.0)
        shopping_total += qty * price

    plan["shopping_items"] = shopping_for_month
    plan["shopping_total"] = shopping_total

    # 3. Compute grand total
    plan["grand_total"] = plan["obligations_total"] + plan["shopping_total"]

    # 4. Warnings
    plan["warnings"] = warnings

    return plan
