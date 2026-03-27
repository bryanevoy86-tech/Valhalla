from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow():
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _up(s: str) -> str:
    return _norm(s).upper()


def _dedupe(tags: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tags or []:
        t2 = _norm(t)
        if t2 and t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def _normalize_milestones(ms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for m in ms or []:
        key = _norm(m.get("key") or "")
        title = _norm(m.get("title") or "")
        if not key or not title:
            continue
        rec = {
            "key": key,
            "title": title,
            "status": m.get("status") or "not_started",
            "due_date": _norm(m.get("due_date") or ""),
            "notes": m.get("notes") or "",
            "updated_at": m.get("updated_at") or None,
        }
        out.append(rec)
    # stable ordering by key
    out.sort(key=lambda x: x["key"])
    return out


def create_entity(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_entities()
    now = _utcnow_iso()
    eid = "ent_" + uuid.uuid4().hex[:12]

    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    rec = {
        "id": eid,
        "name": name,
        "entity_type": payload.get("entity_type") or "trust",
        "country": _up(payload.get("country") or "CA"),
        "region": _up(payload.get("region") or ""),
        "description": payload.get("description") or "",
        "status": payload.get("status") or "not_started",
        "tags": _dedupe(payload.get("tags") or []),
        "milestones": _normalize_milestones(payload.get("milestones") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items.append(rec)
    store.save_entities(items)
    return rec


def list_entities(
    status: Optional[str] = None,
    country: Optional[str] = None,
    entity_type: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = store.list_entities()
    if status:
        items = [e for e in items if e.get("status") == status]
    if country:
        c = _up(country)
        items = [e for e in items if _up(e.get("country") or "") == c]
    if entity_type:
        items = [e for e in items if e.get("entity_type") == entity_type]
    if tag:
        items = [e for e in items if tag in (e.get("tags") or [])]
    return items


def get_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    for e in store.list_entities():
        if e["id"] == entity_id:
            return e
    return None


def patch_entity(entity_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_entities()
    tgt = None
    for e in items:
        if e["id"] == entity_id:
            tgt = e
            break
    if not tgt:
        raise KeyError("entity not found")

    for k in ["name", "entity_type", "description", "status"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name",) else patch.get(k)

    if "country" in patch:
        tgt["country"] = _up(patch.get("country") or tgt.get("country") or "CA")
    if "region" in patch:
        tgt["region"] = _up(patch.get("region") or "")
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}
    if "milestones" in patch:
        tgt["milestones"] = _normalize_milestones(patch.get("milestones") or [])

    tgt["updated_at"] = _utcnow_iso()
    store.save_entities(items)
    return tgt


def upsert_milestone(entity_id: str, milestone: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_entities()
    tgt = None
    for e in items:
        if e["id"] == entity_id:
            tgt = e
            break
    if not tgt:
        raise KeyError("entity not found")

    key = _norm(milestone.get("key") or "")
    title = _norm(milestone.get("title") or "")
    if not key or not title:
        raise ValueError("milestone key and title are required")

    ms = tgt.get("milestones") or []
    found = None
    for m in ms:
        if m.get("key") == key:
            found = m
            break

    now = _utcnow_iso()
    rec = {
        "key": key,
        "title": title,
        "status": milestone.get("status") or "not_started",
        "due_date": _norm(milestone.get("due_date") or ""),
        "notes": milestone.get("notes") or "",
        "updated_at": now,
    }

    if found:
        found.update(rec)
    else:
        ms.append(rec)

    ms.sort(key=lambda x: x.get("key") or "")
    tgt["milestones"] = ms

    # auto-entity status roll-up
    statuses = [m.get("status") for m in ms]
    if any(s == "blocked" for s in statuses):
        tgt["status"] = "blocked"
    elif statuses and all(s == "done" for s in statuses):
        tgt["status"] = "done"
    elif any(s == "in_progress" for s in statuses):
        tgt["status"] = "in_progress"
    else:
        tgt["status"] = tgt.get("status") or "not_started"

    tgt["updated_at"] = now
    store.save_entities(items)

    # optional: mirror to followups if due_date exists (no hard dependency)
    if rec["due_date"]:
        try:
            from backend.app.deals import followups_store  # type: ignore
            followups_store.create_followup({
                "title": f"TRUST/ENTITY: {tgt['name']} — {rec['title']}",
                "due_date": rec["due_date"],
                "priority": "B",
                "status": "open",
                "meta": {"entity_id": entity_id, "milestone_key": rec["key"]},
            })
        except Exception:
            pass

    return tgt


def summary() -> Dict[str, Any]:
    items = store.list_entities()
    by_status: Dict[str, int] = {}
    by_country: Dict[str, int] = {}
    totals: Dict[str, int] = {"entities": len(items)}
    blocked = []

    for e in items:
        s = e.get("status") or "unknown"
        c = _up(e.get("country") or "OTHER")
        by_status[s] = by_status.get(s, 0) + 1
        by_country[c] = by_country.get(c, 0) + 1
        if s == "blocked":
            blocked.append(e)

    return {"totals": totals, "by_status": by_status, "by_country": by_country, "blocked": blocked}
