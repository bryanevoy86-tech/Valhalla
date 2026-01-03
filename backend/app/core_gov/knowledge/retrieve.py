from __future__ import annotations

from typing import Any, Dict, List, Tuple
from . import store

def _score(q: str, text: str) -> int:
    q = q.lower().strip()
    t = (text or "").lower()
    if not q:
        return 0
    score = 0
    for term in [x for x in q.split() if x]:
        if term in t:
            score += 1
    return score

def search(q: str, k: int = 8, tag: str = "") -> Dict[str, Any]:
    if not (q or "").strip():
        raise ValueError("q required")
    k = max(1, min(25, int(k or 8)))
    chunks = store.list_chunks()
    if tag:
        chunks = [c for c in chunks if tag in (c.get("tags") or [])]

    scored: List[Tuple[int, Dict[str, Any]]] = []
    for c in chunks:
        s = _score(q, c.get("text",""))
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [c for _, c in scored[:k]]

    # Return in a "citation-ready" structure
    sources = [{
        "doc_id": c.get("doc_id"),
        "chunk_id": c.get("id"),
        "title": c.get("title",""),
        "source": c.get("source",""),
        "chunk_index": c.get("chunk_index",0),
        "text": c.get("text",""),
    } for c in top]

    return {"q": q, "count": len(sources), "sources": sources}
