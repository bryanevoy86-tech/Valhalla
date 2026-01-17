from __future__ import annotations
from typing import Any, Dict, List
from . import service as dsvc
from .bundles import get as get_bundle

def manifest(bundle_id: str) -> Dict[str, Any]:
    b = get_bundle(bundle_id)
    if not b:
        return {"ok": False, "error": "bundle not found"}

    docs = []
    for did in b.get("doc_ids") or []:
        d = dsvc.get(did)
        if d:
            docs.append({
                "id": d.get("id"),
                "title": d.get("title"),
                "kind": d.get("kind"),
                "file_path": d.get("file_path"),
                "tags": d.get("tags"),
                "links": d.get("links"),
            })
    return {"ok": True, "bundle": b, "docs": docs}
