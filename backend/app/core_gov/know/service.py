from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


_WORD = re.compile(r"[A-Za-z0-9']+")


def _utcnow():
    return datetime.now(timezone.utc)


def _norm(s: str) -> str:
    return (s or "").strip()


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD.findall(text or "") if t]


def _estimate_tokens(text: str) -> int:
    # rough: 4 chars/token
    return max(1, math.ceil(len(text) / 4))


def clean_text(raw: str) -> str:
    t = raw or ""
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[Tuple[int, int, str]]:
    """
    Simple char-based chunking with overlap. Good enough for v1.
    Returns: (char_start, char_end, chunk_text)
    """
    text = text or ""
    if len(text) <= max_chars:
        return [(0, len(text), text)]
    out = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + max_chars)
        chunk = text[i:j]
        out.append((i, j, chunk))
        if j == n:
            break
        i = max(0, j - overlap)
    return out


def _score_terms(query_terms: List[str], chunk_terms: List[str]) -> float:
    if not query_terms:
        return 0.0
    qt = set(query_terms)
    ct = set(chunk_terms)
    hits = len(qt.intersection(ct))
    return hits / max(1, len(qt))


def ingest_doc(title: str, source: str, tags: List[str], content: str, linked: Dict[str, str], meta: Dict[str, Any]) -> Dict[str, Any]:
    docs = store.list_docs()
    chunks = store.list_chunks()

    now = _utcnow()
    doc_id = "know_" + uuid.uuid4().hex[:12]

    doc = {
        "id": doc_id,
        "title": _norm(title),
        "source": _norm(source) or "manual",
        "tags": list(dict.fromkeys([_norm(x) for x in (tags or []) if _norm(x)])),
        "linked": linked or {},
        "meta": meta or {},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    docs.append(doc)

    clean = clean_text(content)
    parts = chunk_text(clean)
    created = 0
    for ord_i, (a, b, txt) in enumerate(parts):
        chunk_id = "chk_" + uuid.uuid4().hex[:14]
        rec = {
            "id": chunk_id,
            "doc_id": doc_id,
            "ord": ord_i,
            "text": txt,
            "char_start": a,
            "char_end": b,
            "tokens_est": _estimate_tokens(txt),
            "created_at": now.isoformat(),
        }
        chunks.append(rec)
        created += 1

    store.save_docs(docs)
    store.save_chunks(chunks)

    # update index incrementally
    _index_chunks([c for c in chunks if c["doc_id"] == doc_id], doc)

    return {"doc": doc, "chunks_created": created}


def _index_chunks(chunk_recs: List[Dict[str, Any]], doc: Dict[str, Any]) -> None:
    idx = store.read_index()
    terms = idx.get("terms", {})
    chunk_meta = idx.get("chunk_meta", {})

    for c in chunk_recs:
        toks = _tokenize(c["text"])
        # store minimal meta for retrieval
        chunk_meta[c["id"]] = {
            "doc_id": doc["id"],
            "ord": c["ord"],
            "title": doc["title"],
            "source": doc["source"],
            "tags": doc.get("tags", []),
            "linked": doc.get("linked", {}),
        }
        for t in set(toks):
            bucket = terms.get(t)
            if bucket is None:
                terms[t] = [c["id"]]
            else:
                if c["id"] not in bucket:
                    bucket.append(c["id"])

    idx["terms"] = terms
    idx["chunk_meta"] = chunk_meta
    store.write_index(idx)


def rebuild_index() -> Dict[str, Any]:
    docs = store.list_docs()
    chunks = store.list_chunks()

    doc_by_id = {d["id"]: d for d in docs}
    terms: Dict[str, List[str]] = {}
    chunk_meta: Dict[str, Any] = {}

    for c in chunks:
        d = doc_by_id.get(c["doc_id"])
        if not d:
            continue
        toks = _tokenize(c["text"])
        chunk_meta[c["id"]] = {
            "doc_id": d["id"],
            "ord": c["ord"],
            "title": d["title"],
            "source": d["source"],
            "tags": d.get("tags", []),
            "linked": d.get("linked", {}),
        }
        for t in set(toks):
            terms.setdefault(t, []).append(c["id"])

    idx = {"terms": terms, "chunk_meta": chunk_meta}
    store.write_index(idx)
    return {"ok": True, "docs_indexed": len(docs), "chunks_indexed": len(chunks), "terms": len(terms)}


def search(query: str, limit: int = 10, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    q = _norm(query)
    if not q:
        return []
    q_terms = _tokenize(q)
    idx = store.read_index()
    terms = idx.get("terms", {})
    meta = idx.get("chunk_meta", {})

    # candidate chunk ids from term buckets
    cand = []
    seen = set()
    for t in q_terms:
        for cid in terms.get(t, []):
            if cid not in seen:
                seen.add(cid)
                cand.append(cid)

    # load chunks for scoring
    chunks = store.list_chunks()
    chunk_by_id = {c["id"]: c for c in chunks}

    hits = []
    for cid in cand:
        c = chunk_by_id.get(cid)
        m = meta.get(cid)
        if not c or not m:
            continue
        if tag:
            if tag not in (m.get("tags") or []):
                continue
        score = _score_terms(q_terms, _tokenize(c["text"]))
        if score <= 0:
            continue
        txt = c["text"]
        snippet = txt[:280].replace("\n", " ").strip()
        hits.append({
            "doc_id": m["doc_id"],
            "doc_title": m.get("title", ""),
            "chunk_id": cid,
            "score": float(score),
            "snippet": snippet,
            "source": m.get("source", ""),
            "tags": m.get("tags", []),
            "linked": m.get("linked", {}),
        })

    hits.sort(key=lambda x: x["score"], reverse=True)
    return hits[: max(1, min(limit, 50))]


def get_doc(doc_id: str) -> Optional[Dict[str, Any]]:
    for d in store.list_docs():
        if d["id"] == doc_id:
            return d
    return None


def get_chunk(chunk_id: str) -> Optional[Dict[str, Any]]:
    for c in store.list_chunks():
        if c["id"] == chunk_id:
            return c
    return None


def ingest_inbox_files(limit: int = 25) -> Dict[str, Any]:
    files = store.list_inbox_files()[: max(0, min(limit, 200))]
    results = []
    for name in files:
        raw = store.read_inbox_file(name)
        clean = clean_text(raw)
        store.move_inbox_to_clean(name, clean)
        r = ingest_doc(
            title=name,
            source=f"inbox:{name}",
            tags=["inbox"],
            content=clean,
            linked={},
            meta={"filename": name},
        )
        results.append(r)
    return {"ingested": len(results), "results": results}
