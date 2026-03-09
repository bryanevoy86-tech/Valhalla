from __future__ import annotations
from typing import Any, Dict, List
from . import store
from .attachments import file_fingerprint

def attach(receipt_id: str, file_path: str) -> Dict[str, Any]:
    items = store.list_items()
    r = next((x for x in items if x.get("id") == receipt_id), None)
    if not r:
        raise KeyError("not found")

    fp = file_fingerprint(file_path=file_path)
    atts = r.get("attachments") or []
    atts.append(fp)
    r["attachments"] = atts
    store.save_items(items)
    return {"receipt_id": receipt_id, "attachment": fp, "count": len(atts)}
