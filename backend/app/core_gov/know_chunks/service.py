from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def chunk_text(source_id: str, text: str, chunk_size: int = 800) -> Dict[str, Any]:
    source_id = (source_id or "").strip()
    if not source_id:
        raise ValueError("source_id required")
    t = (text or "").strip()
    if not t:
        raise ValueError("text required")

    size = max(200, min(5000, int(chunk_size or 800)))
    parts = []
    i = 0
    while i < len(t):
        parts.append(t[i:i+size])
        i += size

    chunks = store.list_chunks()
    created = 0
    for idx, p in enumerate(parts):
        chunks.append({
            "id": store.new_id(),
            "source_id": source_id,
            "idx": idx,
            "text": p,
            "created_at": _utcnow_iso(),
        })
        created += 1
    store.save_chunks(chunks)
    return {"created": created, "source_id": source_id, "chunk_size": size}
