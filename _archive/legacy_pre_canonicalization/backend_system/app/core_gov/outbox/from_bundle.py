from __future__ import annotations
from typing import Any, Dict, List
from backend.app.core_gov.doc_vault.export_manifest import manifest  # type: ignore

def create_from_bundle(bundle_id: str, to: str = "(paste)", channel: str = "email") -> Dict[str, Any]:
    m = manifest(bundle_id=bundle_id)
    if not m.get("ok"):
        return {"outbox": None, "error": m.get("error","manifest failed")}

    b = m.get("bundle") or {}
    docs = m.get("docs") or []
    lines = [f"Document Bundle: {b.get('name','')}", ""]
    for d in docs:
        lines.append(f"- {d.get('title')} [{d.get('kind')}]  path: {d.get('file_path')}")
    body = "\n".join(lines)

    try:
        from backend.app.core_gov.outbox import service as obx  # type: ignore
        msg = obx.create(channel=channel, to=to, subject=f"Docs: {b.get('name','')}", body=body, related={"bundle_id": bundle_id})
        return {"outbox": msg, "count": len(docs)}
    except Exception as e:
        return {"outbox": None, "count": len(docs), "error": f"outbox unavailable: {type(e).__name__}: {e}"}
