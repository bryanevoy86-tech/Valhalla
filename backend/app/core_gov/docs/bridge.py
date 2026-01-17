from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timezone


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def attach_doc_as_source(doc: Dict[str, Any], title: str = "", snippet: str = "") -> Dict[str, Any]:
    """
    Converts a doc into a knowledge source.
    """
    return {
        "source_type": "doc",
        "doc_id": doc.get("id"),
        "title": title or doc.get("title", ""),
        "snippet": snippet or doc.get("body", "")[:200],
        "attached_at": _utcnow_iso(),
        "source_meta": {"doc_keys": list(doc.keys())},
    }


def sanitize_manifest(manifest: Dict[str, Any], level: str = "shareable") -> Dict[str, Any]:
    """
    Light v1 sanitization. Tries to use security module; falls back to field removal.
    """
    try:
        from backend.app.core_gov.security import service as sec_svc  # type: ignore
        return sec_svc.sanitize_manifest(manifest, level=level)
    except Exception:
        # fallback: remove machine refs
        out = dict(manifest or {})
        docs = []
        for d in (out.get("docs") or []):
            d2 = dict(d)
            d2.pop("file_path", None)
            d2.pop("blob_ref", None)
            d2.pop("sha256", None)
            docs.append(d2)
        out["docs"] = docs
        out["sanitized"] = True
        out["sanitized_level"] = level
        return out
