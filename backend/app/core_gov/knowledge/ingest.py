from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from .chunker import chunk_text
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def ingest_doc(doc_id: str, title: str, text: str, tags: List[str] = None, source: str = "") -> Dict[str, Any]:
    if not (doc_id or "").strip():
        raise ValueError("doc_id required")
    if not (text or "").strip():
        raise ValueError("text required")

    tags = tags or []
    parts = chunk_text(text=text)

    chunks = store.list_chunks()
    created = 0
    for idx, p in enumerate(parts):
        chunks.append({
            "id": "chk_" + uuid.uuid4().hex[:12],
            "doc_id": doc_id,
            "title": title or "",
            "source": source or "",
            "tags": tags,
            "chunk_index": idx,
            "text": p,
            "created_at": _utcnow_iso(),
        })
        created += 1

    store.save_chunks(chunks)
    return {"doc_id": doc_id, "created": created}
