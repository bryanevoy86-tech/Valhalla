from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def create_property(payload: Dict[str, Any]) -> Dict[str, Any]:
    address = _norm(payload.get("address") or "")
    city = _norm(payload.get("city") or "")
    if not address or not city:
        raise ValueError("address and city are required")

    now = _utcnow_iso()
    pid = "pi_" + uuid.uuid4().hex[:12]
    rec = {
        "id": pid,
        "address": address,
        "city": city,
        "region": _norm(payload.get("region") or ""),
        "postal": _norm(payload.get("postal") or ""),
        "country": payload.get("country") or "CA",
        "prop_type": payload.get("prop_type") or "SFH",
        "beds": payload.get("beds"),
        "baths": payload.get("baths"),
        "sqft": payload.get("sqft"),
        "lot_sqft": payload.get("lot_sqft"),
        "year_built": payload.get("year_built"),
        "arv_estimate": float(payload.get("arv_estimate") or 0.0),
        "rent_estimate": float(payload.get("rent_estimate") or 0.0),
        "repair_estimate": float(payload.get("repair_estimate") or 0.0),
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_properties()
    items.append(rec)
    store.save_properties(items)
    return rec


def list_properties(country: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_properties()
    if country:
        items = [x for x in items if x.get("country") == country]
    return items


def get_property(pid: str) -> Optional[Dict[str, Any]]:
    for p in store.list_properties():
        if p.get("id") == pid:
            return p
    return None


def create_comp(payload: Dict[str, Any]) -> Dict[str, Any]:
    pid = _norm(payload.get("property_intel_id") or "")
    if not pid:
        raise ValueError("property_intel_id is required")
    if not get_property(pid):
        raise ValueError("property_intel_id not found")

    now = _utcnow_iso()
    cid = "cp_" + uuid.uuid4().hex[:12]
    rec = {
        "id": cid,
        "property_intel_id": pid,
        "address": _norm(payload.get("address") or ""),
        "city": _norm(payload.get("city") or ""),
        "region": _norm(payload.get("region") or ""),
        "country": payload.get("country") or "CA",
        "sold_price": float(payload.get("sold_price") or 0.0),
        "sold_date": _norm(payload.get("sold_date") or ""),
        "beds": payload.get("beds"),
        "baths": payload.get("baths"),
        "sqft": payload.get("sqft"),
        "distance_km": float(payload.get("distance_km") or 0.0),
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_comps()
    items.append(rec)
    store.save_comps(items)
    return rec


def list_comps(property_intel_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_comps()
    if property_intel_id:
        items = [x for x in items if x.get("property_intel_id") == property_intel_id]
    return items


def create_repair(payload: Dict[str, Any]) -> Dict[str, Any]:
    pid = _norm(payload.get("property_intel_id") or "")
    item = _norm(payload.get("item") or "")
    if not pid or not item:
        raise ValueError("property_intel_id and item are required")
    if not get_property(pid):
        raise ValueError("property_intel_id not found")

    now = _utcnow_iso()
    rid = "rp_" + uuid.uuid4().hex[:12]
    rec = {
        "id": rid,
        "property_intel_id": pid,
        "item": item,
        "cost": float(payload.get("cost") or 0.0),
        "category": _norm(payload.get("category") or "other") or "other",
        "tags": payload.get("tags") or [],
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_repairs()
    items.append(rec)
    store.save_repairs(items)
    return rec


def list_repairs(property_intel_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_repairs()
    if property_intel_id:
        items = [x for x in items if x.get("property_intel_id") == property_intel_id]
    return items


def get_intel_summary(property_intel_id: str) -> Dict[str, Any]:
    prop = get_property(property_intel_id)
    if not prop:
        raise ValueError("property not found")

    comps = list_comps(property_intel_id)
    repairs = list_repairs(property_intel_id)
    total_repair_cost = sum(float(r.get("cost") or 0.0) for r in repairs)
    avg_comp_price = sum(float(c.get("sold_price") or 0.0) for c in comps) / len(comps) if comps else 0.0

    return {
        "property_id": property_intel_id,
        "address": prop.get("address", ""),
        "country": prop.get("country", "CA"),
        "comps_count": len(comps),
        "repairs_count": len(repairs),
        "total_repair_cost": total_repair_cost,
        "avg_comp_price": avg_comp_price,
        "arv_estimate": float(prop.get("arv_estimate") or 0.0),
        "rent_estimate": float(prop.get("rent_estimate") or 0.0),
    }
