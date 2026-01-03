from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow():
    return datetime.now(timezone.utc)


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(tags: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tags or []:
        t2 = _norm(t)
        if t2 and t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def create_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_engines()
    now = _utcnow().isoformat()
    eid = "be_" + uuid.uuid4().hex[:12]
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")
    rec = {
        "id": eid,
        "name": name,
        "category": _norm(payload.get("category") or "boring") or "boring",
        "status": payload.get("status") or "planned",
        "description": payload.get("description") or "",
        "pricing_notes": payload.get("pricing_notes") or "",
        "target_city": _norm(payload.get("target_city") or ""),
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items.append(rec)
    store.save_engines(items)
    return rec


def list_engines(status: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_engines()
    if status:
        items = [e for e in items if e.get("status") == status]
    if tag:
        items = [e for e in items if tag in (e.get("tags") or [])]
    return items


def get_engine(engine_id: str) -> Optional[Dict[str, Any]]:
    for e in store.list_engines():
        if e["id"] == engine_id:
            return e
    return None


def patch_engine(engine_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_engines()
    tgt = None
    for e in items:
        if e["id"] == engine_id:
            tgt = e
            break
    if not tgt:
        raise KeyError("engine not found")
    for k in ["name", "category", "status", "description", "pricing_notes", "target_city"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","category","target_city") else patch.get(k)
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}
    tgt["updated_at"] = _utcnow().isoformat()
    store.save_engines(items)
    return tgt


def create_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not get_engine(_norm(payload.get("engine_id") or "")):
        raise KeyError("engine not found")
    runs = store.list_runs()
    now = _utcnow().isoformat()
    rid = "run_" + uuid.uuid4().hex[:12]
    title = _norm(payload.get("title") or "")
    if not title:
        raise ValueError("title is required")
    rec = {
        "id": rid,
        "engine_id": _norm(payload.get("engine_id") or ""),
        "title": title,
        "status": payload.get("status") or "open",
        "customer": _norm(payload.get("customer") or ""),
        "revenue": float(payload.get("revenue") or 0.0),
        "cost": float(payload.get("cost") or 0.0),
        "notes": payload.get("notes") or "",
        "due_date": _norm(payload.get("due_date") or ""),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    runs.append(rec)
    store.save_runs(runs)

    # optional followup creation (no hard dependency)
    if rec["due_date"]:
        try:
            from backend.app.deals import followups_store  # type: ignore
            followups_store.create_followup({
                "title": f"BORING RUN DUE: {rec['title']}",
                "due_date": rec["due_date"],
                "priority": "B",
                "status": "open",
                "meta": {"boring_run_id": rec["id"], "engine_id": rec["engine_id"]},
            })
        except Exception:
            pass

    return rec


def list_runs(engine_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_runs()
    if engine_id:
        items = [r for r in items if r.get("engine_id") == engine_id]
    if status:
        items = [r for r in items if r.get("status") == status]
    return items


def patch_run(run_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_runs()
    tgt = None
    for r in items:
        if r["id"] == run_id:
            tgt = r
            break
    if not tgt:
        raise KeyError("run not found")
    for k in ["title","status","customer","notes","due_date"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("title","customer","due_date") else patch.get(k)
    if "revenue" in patch:
        tgt["revenue"] = float(patch.get("revenue") or 0.0)
    if "cost" in patch:
        tgt["cost"] = float(patch.get("cost") or 0.0)
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}
    tgt["updated_at"] = _utcnow().isoformat()
    store.save_runs(items)
    return tgt


def summary() -> Dict[str, Any]:
    engines = store.list_engines()
    runs = store.list_runs()
    out = []
    for e in engines:
        eruns = [r for r in runs if r.get("engine_id") == e["id"]]
        open_n = sum(1 for r in eruns if r.get("status") == "open")
        done_n = sum(1 for r in eruns if r.get("status") == "done")
        rev = sum(float(r.get("revenue") or 0.0) for r in eruns if r.get("status") in ("open","done"))
        cost = sum(float(r.get("cost") or 0.0) for r in eruns if r.get("status") in ("open","done"))
        out.append({
            "engine_id": e["id"],
            "name": e["name"],
            "status": e.get("status"),
            "runs_open": open_n,
            "runs_done": done_n,
            "revenue_total": float(rev),
            "profit_total": float(rev - cost),
        })
    return {"engines": out}
