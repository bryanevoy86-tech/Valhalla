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


def create_partner(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_partners()
    now = _utcnow().isoformat()
    pid = "par_" + uuid.uuid4().hex[:12]
    name = _norm(payload.get("name") or "")
    if not name:
        raise ValueError("name is required")

    rec = {
        "id": pid,
        "name": name,
        "partner_type": payload.get("partner_type") or "jv",
        "status": payload.get("status") or "active",
        "email": _norm(payload.get("email") or ""),
        "phone": _norm(payload.get("phone") or ""),
        "notes": payload.get("notes") or "",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items.append(rec)
    store.save_partners(items)
    return rec


def list_partners(status: Optional[str] = None, partner_type: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_partners()
    if status:
        items = [p for p in items if p.get("status") == status]
    if partner_type:
        items = [p for p in items if p.get("partner_type") == partner_type]
    if tag:
        items = [p for p in items if tag in (p.get("tags") or [])]
    return items


def get_partner(pid: str) -> Optional[Dict[str, Any]]:
    for p in store.list_partners():
        if p["id"] == pid:
            return p
    return None


def link_deal(partner_id: str, deal_id: str, role: str = "jv", split: str = "", notes: str = "") -> Dict[str, Any]:
    if not get_partner(partner_id):
        raise KeyError("partner not found")
    links = store.list_links()
    now = _utcnow().isoformat()
    rec = {
        "partner_id": partner_id,
        "deal_id": _norm(deal_id),
        "role": _norm(role) or "jv",
        "split": _norm(split),
        "notes": notes or "",
        "created_at": now,
    }
    if not rec["deal_id"]:
        raise ValueError("deal_id required")
    links.append(rec)
    store.save_links(links)
    return rec


def list_links(partner_id: Optional[str] = None, deal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_links()
    if partner_id:
        items = [x for x in items if x.get("partner_id") == partner_id]
    if deal_id:
        items = [x for x in items if x.get("deal_id") == deal_id]
    return items


def dashboard(partner_id: str) -> Dict[str, Any]:
    warnings: List[str] = []
    p = get_partner(partner_id)
    if not p:
        raise KeyError("partner not found")
    links = list_links(partner_id=partner_id)

    # optional: compute deal stats if deals module exists
    computed: Dict[str, Any] = {"linked_deals": len(links)}
    try:
        from backend.app.deals import store as deals_store  # type: ignore
        deals = []
        for l in links:
            try:
                d = deals_store.get_deal(l["deal_id"])
                if d:
                    deals.append(d)
            except Exception:
                continue
        computed["deals_loaded"] = len(deals)
    except Exception:
        warnings.append("deals module not available for computed stats")

    return {"partner": p, "deals": links, "computed": computed, "warnings": warnings}
