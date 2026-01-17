from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


STOP = set("""
a an the and or but if then else when while to from of for in on at by with without into onto
is are was were be been being do does did have has had can could should would may might will
this that these those it its as not no yes you your we our they their
""".split())


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


def _tokenize(text: str) -> List[str]:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    parts = [p for p in text.split() if p and p not in STOP and len(p) > 2]
    return parts


def _approx_tokens(text: str) -> int:
    # crude but stable: ~4 chars per token
    return int(max(1, len(text) / 4))


def create_inbox(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = _norm(payload.get("title") or "")
    if not title:
        raise ValueError("title is required")

    now = _utcnow_iso()
    iid = "ki_" + uuid.uuid4().hex[:12]
    rec = {
        "id": iid,
        "title": title,
        "source_type": payload.get("source_type") or "note",
        "source_ref": _norm(payload.get("source_ref") or ""),
        "raw_text": payload.get("raw_text") or "",
        "cleaned_text": "",
        "stage": "inbox",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_inbox()
    items.append(rec)
    store.save_inbox(items)
    return rec


def list_inbox(stage: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_inbox()
    if stage:
        items = [x for x in items if x.get("stage") == stage]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items


def get_inbox(item_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_inbox():
        if x["id"] == item_id:
            return x
    return None


def _clean_text(raw: str) -> str:
    s = raw or ""
    s = s.replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


def clean_item(item_id: str) -> Dict[str, Any]:
    items = store.list_inbox()
    tgt = None
    for x in items:
        if x["id"] == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("item not found")

    tgt["cleaned_text"] = _clean_text(tgt.get("raw_text") or "")
    tgt["stage"] = "cleaned"
    tgt["updated_at"] = _utcnow_iso()
    store.save_inbox(items)
    return tgt


def chunk_item(item_id: str, max_chunk_chars: int = 900, overlap_chars: int = 120) -> Dict[str, Any]:
    inbox = get_inbox(item_id)
    if not inbox:
        raise KeyError("item not found")

    text = inbox.get("cleaned_text") or inbox.get("raw_text") or ""
    text = _clean_text(text)
    if not text:
        raise ValueError("no text to chunk")

    max_chunk_chars = max(200, int(max_chunk_chars or 900))
    overlap_chars = max(0, int(overlap_chars or 120))
    if overlap_chars >= max_chunk_chars:
        overlap_chars = int(max_chunk_chars / 4)

    chunks = []
    i = 0
    idx = 0
    while i < len(text):
        part = text[i:i + max_chunk_chars]
        cid = "kc_" + uuid.uuid4().hex[:12]
        chunks.append({
            "id": cid,
            "item_id": item_id,
            "chunk_index": idx,
            "text": part,
            "tokens_approx": _approx_tokens(part),
            "meta": {},
            "created_at": _utcnow_iso(),
        })
        idx += 1
        i = i + max_chunk_chars - overlap_chars

    all_chunks = store.list_chunks()
    # remove old chunks for this item
    all_chunks = [c for c in all_chunks if c.get("item_id") != item_id]
    all_chunks.extend(chunks)
    store.save_chunks(all_chunks)

    # update stage
    items = store.list_inbox()
    for x in items:
        if x["id"] == item_id:
            x["stage"] = "chunked"
            x["updated_at"] = _utcnow_iso()
            break
    store.save_inbox(items)
    return {"item_id": item_id, "chunk_count": len(chunks)}


def index_item(item_id: str) -> Dict[str, Any]:
    inbox = get_inbox(item_id)
    if not inbox:
        raise KeyError("item not found")

    chunks = [c for c in store.list_chunks() if c.get("item_id") == item_id]
    if not chunks:
        raise ValueError("no chunks found; run chunk first")

    index_rows = store.list_index()
    index_rows = [r for r in index_rows if r.get("item_id") != item_id]

    for c in chunks:
        tokens = _tokenize(c.get("text") or "")
        freq: Dict[str, int] = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        index_rows.append({
            "item_id": item_id,
            "chunk_id": c.get("id"),
            "freq": freq,
            "title": inbox.get("title",""),
            "source_type": inbox.get("source_type",""),
            "source_ref": inbox.get("source_ref",""),
            "tags": inbox.get("tags") or [],
        })

    store.save_index(index_rows)

    items = store.list_inbox()
    for x in items:
        if x["id"] == item_id:
            x["stage"] = "indexed"
            x["updated_at"] = _utcnow_iso()
            break
    store.save_inbox(items)

    return {"item_id": item_id, "indexed_chunks": len(chunks)}


def process(item_id: str, action: str = "all", max_chunk_chars: int = 900, overlap_chars: int = 120) -> Dict[str, Any]:
    if action in ("clean", "all"):
        clean_item(item_id)
    if action in ("chunk", "all"):
        chunk_item(item_id, max_chunk_chars=max_chunk_chars, overlap_chars=overlap_chars)
    if action in ("index", "all"):
        index_item(item_id)
    return {"ok": True, "item_id": item_id, "action": action}


def _score_query(freq: Dict[str, int], q_tokens: List[str]) -> float:
    score = 0.0
    for t in q_tokens:
        score += float(freq.get(t, 0))
    return score


def search(query: str, top_k: int = 8, item_id: str = "", tag: str = "") -> Dict[str, Any]:
    q = _norm(query)
    if not q:
        raise ValueError("query is required")
    q_tokens = _tokenize(q)

    rows = store.list_index()
    if item_id:
        rows = [r for r in rows if r.get("item_id") == item_id]
    if tag:
        rows = [r for r in rows if tag in (r.get("tags") or [])]

    scored = []
    for r in rows:
        score = _score_query(r.get("freq") or {}, q_tokens)
        if score <= 0:
            continue
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    scored = scored[: int(top_k or 8)]

    # load chunks for snippets
    chunks = store.list_chunks()
    chunk_map = {c.get("id"): c for c in chunks}

    hits = []
    for score, r in scored:
        cid = r.get("chunk_id")
        c = chunk_map.get(cid) or {}
        text = (c.get("text") or "").replace("\n", " ").strip()
        if len(text) > 180:
            text = text[:180] + "…"
        hits.append({
            "item_id": r.get("item_id"),
            "chunk_id": cid,
            "score": float(score),
            "title": r.get("title",""),
            "source_type": r.get("source_type",""),
            "source_ref": r.get("source_ref",""),
            "snippet": text,
        })

    return {"query": q, "hits": hits}
