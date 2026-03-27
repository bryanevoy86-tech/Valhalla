from __future__ import annotations
from typing import Any, Dict

def snapshot() -> Dict[str, Any]:
    # budget targets
    try:
        from backend.app.core_gov.budget import store as bstore  # type: ignore
        b = bstore.get()
    except Exception:
        b = {"categories": {}, "month_income_target": 0.0}

    # bills sum (monthly-ish approximation)
    try:
        from backend.app.core_gov.bills import store as bills_store  # type: ignore
        bills = [x for x in bills_store.list_bills() if x.get("status") == "active"]
    except Exception:
        bills = []

    bills_monthly = 0.0
    for x in bills:
        cad = (x.get("cadence") or "monthly").lower()
        amt = float(x.get("amount") or 0.0)
        if cad == "weekly":
            bills_monthly += amt * 4.0
        elif cad == "yearly":
            bills_monthly += amt / 12.0
        elif cad == "every_n_months":
            n = float(x.get("due_months") or 1.0)
            bills_monthly += (amt / max(1.0, n))
        else:
            bills_monthly += amt

    # ledger month totals (best-effort)
    ledger = {}
    try:
        from backend.app.core_gov.ledger import service as lsvc  # type: ignore
        ledger = lsvc.monthly_summary()  # if you built it; otherwise except
    except Exception:
        ledger = {}

    return {
        "budget": b,
        "bills_monthly_est": round(bills_monthly, 2),
        "ledger_month": ledger,
    }
