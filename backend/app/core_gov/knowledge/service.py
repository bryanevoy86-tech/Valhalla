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


def attach(entity_type: str, entity_id: str, sources: List[Dict[str, Any]], tags: List[str], meta: Dict[str, Any]) -> Dict[str, Any]:
    entity_id = _norm(entity_id)
    if not entity_id:
        raise ValueError("entity_id is required")

    now = _utcnow_iso()
    items = store.list_links()

    existing = None
    for r in items:
        if r.get("entity_type") == entity_type and r.get("entity_id") == entity_id:
            existing = r
            break

    if not existing:
        rid = "kl_" + uuid.uuid4().hex[:12]
        existing = {
            "id": rid,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "sources": [],
            "tags": [],
            "meta": {},
            "created_at": now,
            "updated_at": now,
        }
        items.append(existing)

    # merge sources (simple de-dupe by (source_type, ref))
    seen = set((s.get("source_type"), s.get("ref")) for s in (existing.get("sources") or []))
    for s in sources or []:
        st = s.get("source_type") or "doc"
        ref = _norm(s.get("ref") or "")
        if not ref:
            continue
        k = (st, ref)
        if k in seen:
            continue
        seen.add(k)
        existing["sources"].append({
            "source_type": st,
            "ref": ref,
            "title": _norm(s.get("title") or ""),
            "snippet": s.get("snippet") or "",
            "meta": s.get("meta") or {},
        })

    existing["tags"] = _dedupe((existing.get("tags") or []) + (tags or []))
    existing["meta"] = {**(existing.get("meta") or {}), **(meta or {})}
    existing["updated_at"] = now

    store.save_links(items)
    return existing


def list_links(entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_links()
    if entity_type:
        items = [x for x in items if x.get("entity_type") == entity_type]
    if entity_id:
        items = [x for x in items if x.get("entity_id") == entity_id]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items


def format_citations(sources: List[Dict[str, Any]], style: str = "short") -> List[str]:
    out = []
    idx = 1
    for s in sources or []:
        st = s.get("source_type") or "doc"
        ref = s.get("ref") or ""
        title = (s.get("title") or "").strip()
        snip = (s.get("snippet") or "").strip()

        label = f"[S{idx}]"
        if style == "long":
            line = f"{label} {title or '(untitled)'} — {st}:{ref}"
            if snip:
                # keep small; avoid huge dumps
                sn = snip.replace("\n", " ").strip()
                if len(sn) > 160:
                    sn = sn[:160] + "…"
                line += f" — {sn}"
        else:
            line = f"{label} {title or st}:{ref}"
        out.append(line)
        idx += 1
    return out
