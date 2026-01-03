from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List

def _today_iso() -> str:
    return date.today().isoformat()

def plan(days: int = 14) -> Dict[str, Any]:
    horizon = date.today() + timedelta(days=max(1, min(90, int(days or 14))))
    incomes = []
    try:
        from ..income import store as istore
        incomes = [x for x in istore.list_items() if x.get("status") == "active"]
    except Exception:
        incomes = []

    expected: List[Dict[str, Any]] = []
    for inc in incomes:
        nd = (inc.get("next_date") or "").strip()
        if nd and nd <= horizon.isoformat():
            expected.append({"income_id": inc.get("id"), "name": inc.get("name"), "date": nd, "amount": inc.get("amount"), "currency": inc.get("currency")})

    expected.sort(key=lambda x: x.get("date",""))
    return {"today": _today_iso(), "horizon": horizon.isoformat(), "expected": expected[:5000]}
