"""
Normalizer for lead intake fields - heuristic property type mapping and field cleanup.
"""

from typing import Optional


def norm_type(s: str | None) -> Optional[str]:
    """Normalize property type strings to standard values."""
    if not s:
        return None
    s = s.strip().lower()
    maps = {
        "single family": "SFH",
        "sfh": "SFH",
        "single-family": "SFH",
        "house": "SFH",
        "duplex": "Duplex",
        "triplex": "Triplex",
        "quadplex": "Quadplex",
        "fourplex": "Quadplex",
        "condo": "Condo",
        "condominium": "Condo",
        "apartment": "Apartment",
        "townhouse": "Townhouse",
    }
    return maps.get(s, s.capitalize())


def normalize_lead_fields(payload: dict) -> dict:
    """Heuristic normalization of a raw lead dict."""
    out = {
        "name": payload.get("name") or payload.get("owner") or None,
        "email": payload.get("email") or None,
        "phone": (payload.get("phone") or "").strip() or None,
        "address": payload.get("address") or payload.get("addr") or None,
        "region": payload.get("region") or payload.get("city") or payload.get("area") or None,
        "property_type": norm_type(payload.get("property_type") or payload.get("type")),
        "price": payload.get("price") or payload.get("ask") or None,
        "beds": payload.get("beds") or payload.get("br") or None,
        "baths": payload.get("baths") or payload.get("ba") or None,
        "notes": payload.get("notes") or payload.get("comment") or None,
    }
    return out
