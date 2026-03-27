from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


def _csv_to_set(s: str | None) -> set[str]:
    if not s:
        return set()
    return {x.strip().lower() for x in s.split(",") if x.strip()}


@dataclass
class DealSearch:
    city: str | None = None
    zip: str | None = None
    price: float | None = None
    beds: float | None = None
    baths: float | None = None
    property_type: str | None = None
    tags: set[str] | None = None
    legacy_id: str | None = None


def score_buyer(buyer, q: DealSearch) -> float:
    score = 0.0
    if q.legacy_id and getattr(buyer, "legacy_id", None) != q.legacy_id:
        return 0.0
    markets = _csv_to_set(buyer.markets)
    if q.city and q.city.lower() in markets:
        score += 20
    zips = _csv_to_set(buyer.zips)
    if q.zip and q.zip.lower() in zips:
        score += 20
    price = float(q.price or 0.0)
    if buyer.price_min <= price <= buyer.price_max:
        score += 25
    else:
        span_low = buyer.price_min * 0.9
        span_high = buyer.price_max * 1.1
        if span_low <= price <= span_high:
            score += 10
    if (q.beds or 0) >= (buyer.beds_min or 0) and (q.baths or 0) >= (buyer.baths_min or 0):
        score += 15
    pt = _csv_to_set(buyer.property_types)
    if q.property_type and q.property_type.lower() in pt:
        score += 10
    bt = _csv_to_set(buyer.tags)
    qt = q.tags or set()
    if bt and qt:
        overlap = bt.intersection(qt)
        score += min(10.0, len(overlap) * 5.0)
    if not getattr(buyer, "active", True):
        return 0.0
    return round(score, 2)


def rank_buyers(buyers: Iterable, q: DealSearch, top_k: int = 25):
    ranked = [(b, score_buyer(b, q)) for b in buyers]
    ranked.sort(key=lambda x: x[1], reverse=True)
    return [(b, s) for b, s in ranked if s > 0.0][:top_k]
