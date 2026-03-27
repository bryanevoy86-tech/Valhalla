from __future__ import annotations

from typing import Any, Dict, List


def suggest_funding(days: int = 30) -> Dict[str, Any]:
    warnings: List[str] = []

    # obligations total next N days
    obligations_total = 0.0
    try:
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        ev = cal.next_n_days_calendar(int(days or 30))
        items = (ev or {}).get("items", []) if isinstance(ev, dict) else (ev or [])
        for x in items:
            if x.get("type") == "obligation":
                obligations_total += float(x.get("amount_due") or 0.0)
    except Exception as e:
        warnings.append(f"budget_calendar unavailable: {type(e).__name__}: {e}")

    # shopping estimate next N days (uses open items; includes those without desired_by)
    shopping_total = 0.0
    try:
        from backend.app.core_gov.shopping import service as ssvc  # type: ignore
        sh = ssvc.list_items(status="open")
        for it in sh:
            qty = float(it.get("qty") or 1.0)
            uc = float(it.get("est_unit_cost") or 0.0)
            if uc > 0:
                shopping_total += qty * uc
    except Exception as e:
        warnings.append(f"shopping unavailable: {type(e).__name__}: {e}")

    # suggest vault plan (simple default buckets)
    plan = [
        {"vault_name": "Bills Buffer", "category": "bills", "suggested_amount": float(obligations_total)},
        {"vault_name": "Shopping Buffer", "category": "shopping", "suggested_amount": float(shopping_total)},
        {"vault_name": "Emergency Buffer", "category": "emergency", "suggested_amount": float(max(250.0, obligations_total * 0.10))},
    ]

    return {
        "range_days": int(days or 30),
        "obligations_est": float(obligations_total),
        "shopping_est": float(shopping_total),
        "plan": plan,
        "warnings": warnings,
        "note": "This is a suggestion engine. Tie vaults to real bank sub-accounts later.",
    }
