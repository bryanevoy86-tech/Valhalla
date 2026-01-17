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


def create_partner(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    now = _utcnow_iso()
    pid = "pt_" + uuid.uuid4().hex[:12]
    rec = {
        "id": pid,
        "name": name,
        "partner_type": payload.get("partner_type") or "jv_partner",
        "status": payload.get("status") or "active",
        "tier": payload.get("tier") or "B",
        "email": _norm(payload.get("email") or ""),
        "phone": _norm(payload.get("phone") or ""),
        "location": _norm(payload.get("location") or ""),
        "notes": payload.get("notes") or "",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_partners()
    items.append(rec)
    store.save_partners(items)
    return rec


def list_partners(status: Optional[str] = None, partner_type: Optional[str] = None, tier: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_partners()
    if status:
        items = [x for x in items if x.get("status") == status]
    if partner_type:
        items = [x for x in items if x.get("partner_type") == partner_type]
    if tier:
        items = [x for x in items if x.get("tier") == tier]
    items.sort(key=lambda x: (x.get("tier","B"), x.get("name","")))
    return items


def get_partner(pid: str) -> Optional[Dict[str, Any]]:
    for x in store.list_partners():
        if x["id"] == pid:
            return x
    return None


def patch_partner(pid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_partners()
    tgt = None
    for x in items:
        if x["id"] == pid:
            tgt = x
            break
    if not tgt:
        raise KeyError("partner not found")

    for k in ["name","partner_type","status","tier","email","phone","location"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("name","email","phone","location") else patch.get(k)
    if "notes" in patch:
        tgt["notes"] = patch.get("notes") or ""
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_partners(items)
    return tgt


def create_note(payload: Dict[str, Any]) -> Dict[str, Any]:
    partner_id = _norm(payload.get("partner_id") or "")
    title = _norm(payload.get("title") or "")
    if not partner_id:
        raise ValueError("partner_id is required")
    if not title:
        raise ValueError("title is required")
    if not get_partner(partner_id):
        raise KeyError("partner not found")

    now = _utcnow_iso()
    nid = "pn_" + uuid.uuid4().hex[:12]
    rec = {
        "id": nid,
        "partner_id": partner_id,
        "title": title,
        "body": payload.get("body") or "",
        "deal_id": _norm(payload.get("deal_id") or ""),
        "visibility": payload.get("visibility") or "internal",
        "meta": payload.get("meta") or {},
        "created_at": now,
    }
    items = store.list_notes()
    items.append(rec)
    store.save_notes(items)
    return rec


def list_notes(partner_id: Optional[str] = None, visibility: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_notes()
    if partner_id:
        items = [x for x in items if x.get("partner_id") == partner_id]
    if visibility:
        items = [x for x in items if x.get("visibility") == visibility]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items


def dashboard() -> Dict[str, Any]:
    partners = store.list_partners()
    notes = store.list_notes()

    totals = {"partners": len(partners), "notes": len(notes)}
    by_type: Dict[str, int] = {}
    for p in partners:
        t = p.get("partner_type") or "other"
        by_type[t] = by_type.get(t, 0) + 1

    recent_partners = sorted(partners, key=lambda x: x.get("updated_at",""), reverse=True)[:8]
    recent_notes = sorted(notes, key=lambda x: x.get("created_at",""), reverse=True)[:10]

    return {"totals": totals, "by_type": by_type, "recent_partners": recent_partners, "recent_notes": recent_notes}
