from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional

from app.core_gov.deals.store import add_deal, load_deals
from app.core_gov.deals.models import DealIn

ALLOWED_SOURCES = {"seed", "public", "real"}

EXPORT_FIELDS = [
    "id","created_at_utc","updated_at_utc",
    "country","province_state","city","address","postal_zip",
    "strategy","property_type","bedrooms","bathrooms","sqft",
    "arv","asking_price","est_repairs","mao","est_rent_monthly",
    "seller_motivation","seller_reason","timeline_days",
    "stage","lead_source","tags","notes",
]

def _coerce_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None

def _coerce_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except Exception:
        return None

def _coerce_tags(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    s = str(v).strip()
    if not s:
        return []
    # support "a,b,c" or "a|b|c"
    sep = "|" if "|" in s else ","
    return [t.strip() for t in s.split(sep) if t.strip()]

def _normalize_row(row: dict[str, Any], forced_source: str | None = None) -> dict[str, Any]:
    # map common headers
    def g(*keys: str):
        for k in keys:
            if k in row and row[k] not in (None, ""):
                return row[k]
        return None

    payload = {
        "country": (g("country","Country") or "CA").strip(),
        "province_state": (g("province_state","state","State","province","Province") or "MB").strip(),
        "city": (g("city","City") or "").strip() or "Unknown",
        "address": g("address","Address"),
        "postal_zip": g("postal_zip","zip","Zip","postal","Postal"),
        "strategy": (g("strategy","Strategy") or "wholesale").strip().lower(),
        "property_type": (g("property_type","PropertyType","type") or "sfh").strip().lower(),
        "bedrooms": _coerce_int(g("bedrooms","beds","Beds")),
        "bathrooms": _coerce_float(g("bathrooms","baths","Baths")),
        "sqft": _coerce_int(g("sqft","Sqft","square_feet")),
        "arv": _coerce_float(g("arv","ARV")),
        "asking_price": _coerce_float(g("asking_price","ask","Ask","price","Price")),
        "est_repairs": _coerce_float(g("est_repairs","repairs","Repairs")),
        "mao": _coerce_float(g("mao","MAO")),
        "est_rent_monthly": _coerce_float(g("est_rent_monthly","rent","Rent")),
        "seller_motivation": (g("seller_motivation","motivation","Motivation") or "unknown").strip().lower(),
        "seller_reason": g("seller_reason","reason","Reason"),
        "timeline_days": _coerce_int(g("timeline_days","timeline","TimelineDays")),
        "stage": (g("stage","Stage") or "new").strip().lower(),
        "lead_source": (forced_source or g("lead_source","source","Source") or "real").strip().lower(),
        "tags": _coerce_tags(g("tags","Tags")),
        "notes": g("notes","Notes"),
        "meta": {},
    }

    if payload["lead_source"] not in ALLOWED_SOURCES:
        payload["lead_source"] = "real"

    # Validate with Pydantic (will raise if required fields missing)
    DealIn(**payload)
    return payload

def import_json(items: list[dict[str, Any]], forced_source: str | None = None) -> dict[str, Any]:
    created = 0
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(items):
        try:
            payload = _normalize_row(row, forced_source=forced_source)
            add_deal(payload)
            created += 1
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})
    return {"created": created, "errors": errors[:50]}

def import_csv_text(csv_text: str, forced_source: str | None = None) -> dict[str, Any]:
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    return import_json(rows, forced_source=forced_source)

def export_json(limit: int = 5000) -> list[dict[str, Any]]:
    items = load_deals()
    return items[-limit:]

def export_csv(limit: int = 5000) -> str:
    items = export_json(limit=limit)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    w.writeheader()
    for d in items:
        row = dict(d)
        row["tags"] = "|".join(d.get("tags") or [])
        w.writerow(row)
    return out.getvalue()
