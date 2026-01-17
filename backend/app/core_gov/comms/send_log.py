from __future__ import annotations
from typing import Any, Dict
from . import store

def mark_sent(draft_id: str, channel: str = "", result: str = "sent") -> Dict[str, Any]:
    drafts = store.list_drafts()
    d = next((x for x in drafts if x.get("id") == draft_id), None)
    if not d:
        raise KeyError("not found")
    d["status"] = "sent"
    d["sent_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    if channel:
        d["channel"] = channel
    d["result"] = result
    d["updated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    store.save_drafts(drafts)
    return d
