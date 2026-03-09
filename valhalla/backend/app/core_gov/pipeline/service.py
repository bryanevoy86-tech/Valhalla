from __future__ import annotations
from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List
from . import store

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def run_for_deal(deal_id: str, kind: str = "sms", tone: str = "neutral", to: str = "", create_followup_days: int = 2) -> Dict[str, Any]:
    warnings: List[str] = []
    # build message body from comms module
    try:
        from backend.app.core_gov.comms.deal_message import build as build_msg  # type: ignore
        built = build_msg(deal_id=deal_id, kind=kind, tone=tone)
    except Exception as e:
        built = {"ok": False, "error": f"comms build unavailable: {type(e).__name__}"}

    if not built.get("ok"):
        return {"ok": False, "error": built.get("error","build failed")}

    body = built.get("body") or ""

    # create comms draft
    draft = None
    try:
        from backend.app.core_gov.comms.router import create as create_draft  # type: ignore
        draft = create_draft(kind=kind, to=to, subject="", body=body, meta={"deal_id": deal_id})
    except Exception as e:
        warnings.append(f"draft create failed: {type(e).__name__}: {e}")

    # create followup
    followup = None
    try:
        from backend.app.followups import store as fstore  # type: ignore
        due = (date.today() + timedelta(days=max(0, int(create_followup_days or 2)))).isoformat()
        followup = fstore.create_followup({"type":"deal", "title": f"Follow up on deal {deal_id}", "due_date": due, "status":"open", "meta":{"deal_id": deal_id}})
    except Exception as e:
        warnings.append(f"followup create failed: {type(e).__name__}: {e}")

    # log run
    rec = {
        "id": store.new_id(),
        "deal_id": deal_id,
        "kind": kind,
        "tone": tone,
        "to": to,
        "draft_id": (draft or {}).get("id") if isinstance(draft, dict) else None,
        "followup": followup,
        "created_at": _utcnow(),
        "warnings": warnings,
    }
    runs = store.list_runs()
    runs.append(rec)
    store.save_runs(runs)

    return {"ok": True, "run": rec, "draft": draft, "warnings": warnings}
