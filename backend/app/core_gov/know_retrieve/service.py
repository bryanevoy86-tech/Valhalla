from __future__ import annotations
from typing import Any, Dict, List

def search(query: str, limit: int = 8) -> Dict[str, Any]:
    q = (query or "").strip().lower()
    if not q:
        return {"query": query, "hits": []}

    try:
        from ..know_chunks import store as cstore
        chunks = cstore.list_chunks()
    except Exception:
        chunks = []

    hits: List[Dict[str, Any]] = []
    for c in chunks:
        txt = (c.get("text") or "").lower()
        if q in txt:
            hits.append({
                "source_id": c.get("source_id"),
                "chunk_id": c.get("id"),
                "idx": c.get("idx"),
                "snippet": (c.get("text") or "")[:400],
            })

    hits = hits[:max(1, min(50, int(limit or 8)))]
    return {"query": query, "hits": hits}
