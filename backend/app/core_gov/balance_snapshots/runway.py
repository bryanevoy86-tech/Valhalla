from __future__ import annotations
from typing import Any, Dict

def estimate(account_id: str, days_window: int = 30) -> Dict[str, Any]:
    out: Dict[str, Any] = {"account_id": account_id, "latest_balance": None, "monthly_obligations_est": None, "runway_months_est": None, "notes": []}

    try:
        from backend.app.core_gov.balance_snapshots.service import list_recent
        snaps = list_recent(account_id=account_id, limit=1)
        if snaps:
            out["latest_balance"] = float(snaps[0].get("balance") or 0.0)
    except Exception as e:
        out["notes"].append(f"balances unavailable: {type(e).__name__}")

    try:
        from backend.app.core_gov.budget_obligations import store as obstore
        obs = [x for x in obstore.list_items() if x.get("status") == "active"]
        monthly = 0.0
        for ob in obs:
            amt = float(ob.get("amount") or 0.0)
            freq = (ob.get("frequency") or "monthly").lower()
            if freq == "weekly":
                monthly += amt * 4.33
            elif freq == "biweekly":
                monthly += amt * 2.165
            elif freq == "monthly":
                monthly += amt
            elif freq == "quarterly":
                monthly += amt / 3.0
            elif freq == "yearly":
                monthly += amt / 12.0
            elif freq == "one_time":
                monthly += 0.0
        out["monthly_obligations_est"] = round(monthly, 2)
    except Exception as e:
        out["notes"].append(f"obligations unavailable: {type(e).__name__}")

    if out["latest_balance"] is not None and out["monthly_obligations_est"] not in (None, 0):
        out["runway_months_est"] = round(float(out["latest_balance"]) / float(out["monthly_obligations_est"]), 2)

    return out
