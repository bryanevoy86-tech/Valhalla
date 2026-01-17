from __future__ import annotations

from app.core_gov.go.service import next_step
from app.core_gov.knowledge.link_store import load_links
from app.core_gov.knowledge.search import search_docs
from app.core_gov.knowledge.store import load_manifest

def _manifest_index():
    m = load_manifest()
    return {d.get("id"): d for d in m if d.get("id")}

def next_step_with_sources() -> dict:
    nxt = next_step().model_dump()
    step = (nxt.get("next_step") or {})
    step_id = step.get("id")

    sources = []
    if step_id:
        links = load_links()
        ids = links.get("by_step", {}).get(step_id, []) or []
        idx = _manifest_index()
        for doc_id in ids:
            d = idx.get(doc_id)
            if d:
                sources.append({
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "file_name": d.get("file_name"),
                    "tags": d.get("tags") or [],
                    "truth_level": d.get("truth_level"),
                    "version": d.get("version"),
                    "source": d.get("source"),
                })

    # Optional: suggestions based on step title keywords (very light)
    q = (step.get("title") or "").split(":")[0][:40]
    suggestions = []
    if q:
        suggestions = search_docs(q=q, limit=5)

    return {
        "next": nxt,
        "sources": sources,
        "suggestions": suggestions,
    }
