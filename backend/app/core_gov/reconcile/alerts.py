from __future__ import annotations
from typing import Any, Dict, List

def push_missing_alerts(missing: List[Dict[str, Any]]) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    for m in missing[:100]:
        title = f"PAYMENT MISSING: {m.get('name')} due {m.get('date')}"
        notes = f"payment_id={m.get('payment_id')} amount={m.get('amount')} {m.get('currency')}"
        try:
            from backend.app.core_gov.alerts import store as astore  # type: ignore
            if hasattr(astore, "create"):
                astore.create(title=title, kind="payment", severity="high", notes=notes)  # type: ignore
                created += 1
                continue
        except Exception as e:
            pass
        try:
            from backend.app.core_gov.reminders import service as rsvc  # type: ignore
            rsvc.create(title=title, due_date=str(m.get("date") or ""), kind="payment", notes=notes)
            created += 1
        except Exception as e:
            warnings.append(f"reminders failed: {type(e).__name__}")
    return {"created": created, "warnings": warnings}
