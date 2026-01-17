from __future__ import annotations
from typing import Any, Dict
from . import store

def month_summary(prefix: str) -> Dict[str, Any]:
    # prefix = "YYYY-MM"
    tx = [t for t in store.list_tx() if (t.get("date","").startswith(prefix))]
    income = sum(float(t.get("amount") or 0.0) for t in tx if t.get("kind") == "income")
    expense = sum(float(t.get("amount") or 0.0) for t in tx if t.get("kind") == "expense")
    net = income - expense

    by_cat: Dict[str, float] = {}
    for t in tx:
        if t.get("kind") != "expense":
            continue
        c = t.get("category") or "uncategorized"
        by_cat[c] = round(by_cat.get(c, 0.0) + float(t.get("amount") or 0.0), 2)

    cats = [{"category": k, "total": v} for k, v in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)]
    return {"month": prefix, "income": round(income,2), "expense": round(expense,2), "net": round(net,2), "expense_by_category": cats}
