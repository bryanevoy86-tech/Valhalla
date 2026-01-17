from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import store


def _utcnow():
    return datetime.now(timezone.utc)


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


def create_property(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_properties()
    now = _utcnow().isoformat()
    pid = "prop_" + uuid.uuid4().hex[:12]

    country = _up(payload.get("country") or "CA")
    if country not in ("CA", "US"):
        raise ValueError("country must be CA or US")

    rec = {
        "id": pid,
        "country": country,
        "region": _up(payload.get("region") or ""),
        "city": _norm(payload.get("city") or ""),
        "address": _norm(payload.get("address") or ""),
        "postal": _norm(payload.get("postal") or ""),
        "beds": payload.get("beds"),
        "baths": payload.get("baths"),
        "sqft": payload.get("sqft"),
        "year_built": payload.get("year_built"),
        "deal_id": payload.get("deal_id"),
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }
    items.append(rec)
    store.save_properties(items)
    return rec


def list_properties(country: Optional[str] = None, region: Optional[str] = None, deal_id: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_properties()
    if country:
        items = [p for p in items if p.get("country") == _up(country)]
    if region:
        items = [p for p in items if (p.get("region") or "") == _up(region)]
    if deal_id:
        items = [p for p in items if p.get("deal_id") == deal_id]
    if tag:
        items = [p for p in items if tag in (p.get("tags") or [])]
    return items


def get_property(pid: str) -> Optional[Dict[str, Any]]:
    for p in store.list_properties():
        if p["id"] == pid:
            return p
    return None


def neighborhood_rating(payload: Dict[str, Any]) -> Dict[str, Any]:
    # v1 placeholder heuristics: you can replace later with real sources.
    country = _up(payload.get("country") or "CA")
    region = _up(payload.get("region") or "")
    city = _norm(payload.get("city") or "")
    postal = _norm(payload.get("postal") or "")

    reasons = ["placeholder rating (no external data yet)"]
    score = 0.55

    if country == "CA":
        reasons.append("CA model baseline")
        if region in ("ON", "BC"):
            score += 0.05
            reasons.append(f"region {region} slightly higher baseline")
    if country == "US":
        reasons.append("US model baseline")

    if city:
        score += 0.02
        reasons.append("city provided (+signal)")
    if postal:
        score += 0.02
        reasons.append("postal/zip provided (+signal)")

    score = max(0.0, min(1.0, score))
    band = "B"
    if score >= 0.75:
        band = "A"
    elif score >= 0.55:
        band = "B"
    elif score >= 0.40:
        band = "C"
    else:
        band = "D"

    return {"score": float(score), "band": band, "reasons": reasons, "placeholders": True}


def comps(req: Dict[str, Any]) -> Dict[str, Any]:
    # no scraping yet. just structure.
    notes = [
        "comps placeholder: provide your own comps list later",
        "future: integrate MLS/PropStream/HouseSigma/Realtor/Zillow sources via connectors",
    ]
    return {"placeholders": True, "suggested_arv": None, "comps": [], "notes": notes}


def rent_repairs(req: Dict[str, Any]) -> Dict[str, Any]:
    notes = [
        "rent/repairs placeholder: provide rent comps + repair line-items later",
        "future: integrate rentometer/market sources and your repair calculator packs",
    ]
    repair_range = {"low": None, "high": None, "currency": "CAD"}
    if _up(req.get("country") or "CA") == "US":
        repair_range["currency"] = "USD"
    return {"placeholders": True, "suggested_rent": None, "repair_range": repair_range, "notes": notes}
