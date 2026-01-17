from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

def daily_guard(days_ahead: int = 7) -> Dict[str, Any]:
    warnings: List[str] = []
    actions: List[Dict[str, Any]] = []

    try:
        from backend.app.core_gov.budget_calendar import service as calsvc  # type: ignore
        cal = calsvc.project(days_ahead=int(days_ahead or 7))
        for it in (cal.get("items") or [])[:200]:
            if it.get("autopay_status") != "on":
                actions.append({
                    "type": "bill_due",
                    "severity": "high",
                    "title": f"Bill due: {it.get('name','')}",
                    "due_date": it.get("date",""),
                    "amount": it.get("amount", 0.0),
                    "hint": "Set autopay OR schedule payment reminder.",
                })
    except Exception as e:
        warnings.append(f"budget_calendar unavailable: {type(e).__name__}: {e}")

    try:
        from backend.app.core_gov.house_inventory import service as invsvc  # type: ignore
        low = invsvc.low_stock()
        for x in low[:100]:
            actions.append({
                "type": "low_stock",
                "severity": "normal" if (x.get("priority","normal") != "high") else "high",
                "title": f"Low stock: {x.get('name','')}",
                "location": x.get("location",""),
                "hint": "Add to reorder list or create purchase task.",
            })
    except Exception as e:
        warnings.append(f"house_inventory unavailable: {type(e).__name__}: {e}")

    try:
        from backend.app.core_gov.bills_buffer import service as bbsvc  # type: ignore
        need = bbsvc.required_buffer(days=30)
        required = float(need.get("required") or 0.0)
        current = 0.0
        try:
            from backend.app.core_gov.vaults import service as vsvc  # type: ignore
            vaults = vsvc.list_items()
            buf = next((v for v in vaults if (v.get("vault_type","") == "bills_buffer" or v.get("name","").lower() == "bills buffer")), None)
            if buf:
                current = float(buf.get("balance") or 0.0)
        except Exception:
            pass

        if required > 0 and current < required:
            actions.append({
                "type": "buffer_short",
                "severity": "high",
                "title": "Bills Buffer shortfall",
                "required": required,
                "current": current,
                "short": float(required - current),
                "hint": "Top up Bills Buffer before next due window.",
            })
    except Exception as e:
        warnings.append(f"bills_buffer unavailable: {type(e).__name__}: {e}")

    sev = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    actions.sort(key=lambda x: (sev.get(x.get("severity","normal"), 9), x.get("title","")))
    return {"date": date.today().isoformat(), "actions": actions[:400], "warnings": warnings}
