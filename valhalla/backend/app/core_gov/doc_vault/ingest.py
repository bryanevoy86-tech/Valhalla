from __future__ import annotations
from typing import Any, Dict, List

def enqueue(doc_id: str) -> Dict[str, Any]:
    try:
        from . import service as dsvc
        d = dsvc.get(doc_id)
    except Exception:
        d = None
    if not d:
        return {"ok": False, "error": "doc not found"}

    try:
        from backend.app.core_gov.know_inbox import store as kstore  # type: ignore
        rec = {
            "id": kstore.new_id(),
            "title": d.get("title",""),
            "file_path": d.get("file_path",""),
            "tags": d.get("tags") or [],
            "notes": "enqueued from doc_vault",
            "status": "new",
        }
        items = kstore.list_items()
        items.append(rec)
        kstore.save_items(items)
        return {"ok": True, "inbox_item": rec}
    except Exception as e:
        return {"ok": False, "error": f"know_inbox unavailable: {type(e).__name__}: {e}"}
