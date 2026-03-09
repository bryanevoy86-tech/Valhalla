from __future__ import annotations
from typing import Any, Dict

def create_from_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.bills import store as bstore  # type: ignore
    except Exception:
        return {"ok": False, "error": "bills module not available"}

    name = str(candidate.get("name") or "Bill")
    payee = str(candidate.get("payee") or "")
    amount = float(candidate.get("amount") or 0.0)
    currency = str(candidate.get("currency") or "CAD")
    cadence = str(candidate.get("cadence") or "monthly")
    due_day = int(candidate.get("due_day") or 1)
    notes = str(candidate.get("notes") or "")

    if hasattr(bstore, "create"):
        try:
            rec = bstore.create(name=name, payee=payee, amount=amount, currency=currency, cadence=cadence, due_day=due_day, notes=notes)  # type: ignore
            return {"ok": True, "bill": rec}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    return {"ok": False, "error": "bills.store.create not found"}
