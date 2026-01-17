from __future__ import annotations
from typing import Any, Dict, List
from . import store

def mark_sent(run_id: str, channel: str = "", result: str = "sent") -> Dict[str, Any]:
    runs = store.list_runs()
    r = next((x for x in runs if x.get("id") == run_id), None)
    if not r:
        return {"ok": False, "error": "run not found"}
    draft_id = r.get("draft_id")
    if not draft_id:
        return {"ok": False, "error": "run has no draft_id"}

    try:
        from backend.app.core_gov.comms.send_log import mark_sent as ms  # type: ignore
        d = ms(draft_id=draft_id, channel=channel, result=result)
    except Exception as e:
        return {"ok": False, "error": f"mark_sent failed: {type(e).__name__}: {e}"}

    r["sent"] = True
    r["sent_channel"] = channel
    store.save_runs(runs)
    return {"ok": True, "run": r, "draft": d}
