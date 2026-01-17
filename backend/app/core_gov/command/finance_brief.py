from __future__ import annotations

from datetime import date
from typing import Any, Dict, List


def _ym_today() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"


def finance_brief(month: str = "") -> Dict[str, Any]:
    month = month or _ym_today()
    warnings: List[str] = []

    actuals = {}
    try:
        from backend.app.core_gov.budget import actuals as act  # type: ignore
        actuals = act.month_actuals(month)
        warnings += actuals.get("warnings", [])
    except Exception as e:
        warnings.append(f"actuals unavailable: {type(e).__name__}: {e}")

    unreconciled = 0
    try:
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        unreconciled = len(bsvc.list_txns(status="new", limit=500))
    except Exception as e:
        warnings.append(f"bank unavailable: {type(e).__name__}: {e}")

    upcoming = []
    try:
        from backend.app.core_gov.calendar import service as calsvc  # type: ignore
        upcoming = (calsvc.feed(days=14) or {}).get("items", [])
    except Exception as e:
        warnings.append(f"calendar unavailable: {type(e).__name__}: {e}")

    vault_plan = {}
    try:
        from backend.app.core_gov.vaults import allocator  # type: ignore
        vault_plan = allocator.suggest_funding(days=30)
        warnings += vault_plan.get("warnings", [])
    except Exception as e:
        warnings.append(f"vaults unavailable: {type(e).__name__}: {e}")

    return {
        "month": month,
        "actuals": actuals,
        "bank_unreconciled_count": int(unreconciled),
        "upcoming_14_days": upcoming[:30],
        "vault_funding_suggestion": vault_plan,
        "warnings": warnings,
        "next_actions": [
            "Import bank CSV → run reconcile batch",
            "Categorize new receipts",
            "Fund Bills Buffer and Shopping Buffer",
        ],
    }
