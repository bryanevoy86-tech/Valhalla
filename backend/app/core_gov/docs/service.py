from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(xs: List[str]) -> List[str]:
    out, seen = [], set()
    for x in xs or []:
        x2 = _norm(x)
        if x2 and x2 not in seen:
            seen.add(x2)
            out.append(x2)
    return out


def create_doc(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = _norm(payload.get("title") or "")
    if not title:
        raise ValueError("title is required")

    now = _utcnow_iso()
    did = "dc_" + uuid.uuid4().hex[:12]
    rec = {
        "id": did,
        "title": title,
        "doc_type": payload.get("doc_type") or "other",
        "visibility": payload.get("visibility") or "internal",
        "file_path": _norm(payload.get("file_path") or ""),
        "blob_ref": _norm(payload.get("blob_ref") or ""),
        "mime": _norm(payload.get("mime") or ""),
        "sha256": _norm(payload.get("sha256") or ""),
        "tags": _dedupe(payload.get("tags") or []),
        "links": payload.get("links") or {},
        "notes": payload.get("notes") or "",
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_docs()
    items.append(rec)
    store.save_docs(items)
    return rec


def list_docs(doc_type: Optional[str] = None, visibility: Optional[str] = None, tag: Optional[str] = None, entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_docs()
    if doc_type:
        items = [x for x in items if x.get("doc_type") == doc_type]
    if visibility:
        items = [x for x in items if x.get("visibility") == visibility]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    if entity_type and entity_id:
        items = [x for x in items if (x.get("links") or {}).get(entity_type) == entity_id]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items


def get_doc(doc_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_docs():
        if x["id"] == doc_id:
            return x
    return None


def patch_doc(doc_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_docs()
    tgt = None
    for x in items:
        if x["id"] == doc_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("doc not found")

    for k in ["title","doc_type","visibility","file_path","blob_ref","mime","sha256"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("title","file_path","blob_ref","mime","sha256") else patch.get(k)
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "links" in patch:
        tgt["links"] = patch.get("links") or {}
    if "notes" in patch:
        tgt["notes"] = patch.get("notes") or ""
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_docs(items)
    return tgt


def create_bundle(name: str, doc_ids: List[str], include_links: bool = True, include_notes: bool = True, meta: Dict[str, Any] = None) -> Dict[str, Any]:
    name = _norm(name)
    if not name:
        raise ValueError("name is required")
    meta = meta or {}

    # validate docs exist
    docs = []
    for did in doc_ids or []:
        d = get_doc(did)
        if not d:
            raise KeyError(f"doc not found: {did}")
        docs.append(d)

    manifest_docs = []
    for d in docs:
        row = {
            "id": d["id"],
            "title": d.get("title",""),
            "doc_type": d.get("doc_type","other"),
            "visibility": d.get("visibility","internal"),
            "file_path": d.get("file_path",""),
            "blob_ref": d.get("blob_ref",""),
            "mime": d.get("mime",""),
            "sha256": d.get("sha256",""),
            "tags": d.get("tags") or [],
        }
        if include_links:
            row["links"] = d.get("links") or {}
        if include_notes:
            row["notes"] = d.get("notes") or ""
        manifest_docs.append(row)

    now = _utcnow_iso()
    bid = "bd_" + uuid.uuid4().hex[:12]
    bundle = {
        "id": bid,
        "name": name,
        "manifest": {
            "bundle_id": bid,
            "name": name,
            "created_at": now,
            "doc_count": len(manifest_docs),
            "docs": manifest_docs,
            "meta": meta,
        },
        "created_at": now,
    }

    bundles = store.list_bundles()
    bundles.append(bundle)
    store.save_bundles(bundles)
    return bundle
