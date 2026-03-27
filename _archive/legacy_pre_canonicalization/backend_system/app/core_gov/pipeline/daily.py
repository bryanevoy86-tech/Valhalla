from __future__ import annotations
from datetime import date
from typing import Any, Dict, List
from .service import run_for_deal

def tick(limit: int = 10) -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    try:
        from backend.app.followups import store as fstore  # type: ignore
        q = fstore.list_followups(status="open", limit=500) if hasattr(fstore, "list_followups") else []
    except Exception as e:
        return {"created": 0, "warnings": [f"followups unavailable: {type(e).__name__}: {e}"]}

    today = date.today().isoformat()
    due = [x for x in q if (x.get("due_date") or "") and x.get("due_date") <= today]
    due = due[:max(1, min(50, int(limit or 10)))]

    for f in due:
        deal_id = ((f.get("meta") or {}).get("deal_id") or "").strip()
        if not deal_id:
            continue
        out = run_for_deal(deal_id=deal_id, kind="sms", tone="neutral", to="", create_followup_days=2)
        if out.get("ok"):
            created += 1
        else:
            warnings.append(out.get("error","pipeline run failed"))

    return {"created": created, "warnings": warnings}
