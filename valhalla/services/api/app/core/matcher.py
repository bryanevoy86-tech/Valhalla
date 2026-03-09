"""
Buyer-Deal matching core logic with fuzzy scoring.
"""

from typing import List, Tuple
from decimal import Decimal
from rapidfuzz import fuzz

def _split_csv(s: str | None) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]

def score_buyer_vs_deal(buyer, deal) -> Tuple[float, List[str]]:
    """Return score in [0,1] and list of reasons."""
    score = 0.0
    reasons: List[str] = []

    # Region match (soft fuzzy)
    if buyer.regions and deal.region:
        regions = _split_csv(buyer.regions)
        region_scores = [fuzz.token_set_ratio(r.lower(), deal.region.lower())/100.0 for r in regions]
        rs = max(region_scores or [0.0])
        if rs >= 0.6:
            score += 0.25 * rs
            reasons.append(f"region≈{deal.region} ({rs:.2f})")

    # Type match (exact from list)
    if buyer.property_types and deal.property_type:
        types = {t.lower() for t in _split_csv(buyer.property_types)}
        if deal.property_type.lower() in types:
            score += 0.25
            reasons.append(f"type={deal.property_type}")

    # Price window
    if deal.price is not None:
        lo = float(buyer.min_price or 0)
        hi = float(buyer.max_price or 10**12)
        p = float(deal.price)
        if lo <= p <= hi:
            score += 0.25
            reasons.append("price in range")
        else:
            # soft decay if near boundary (±10%)
            width = max(1.0, 0.1 * max(hi, 1.0))
            dist = 0.0
            if p < lo:
                dist = (lo - p) / width
            elif p > hi:
                dist = (p - hi) / width
            if dist < 1.0:
                bonus = 0.15 * (1.0 - dist)
                score += max(0.0, bonus)
                reasons.append("price near range")

    # Beds/baths minima
    ok_beds = (buyer.min_beds or 0) <= (deal.beds or 0)
    ok_baths = (buyer.min_baths or 0) <= (deal.baths or 0)
    if ok_beds:
        score += 0.15
        reasons.append("beds ok")
    if ok_baths:
        score += 0.10
        reasons.append("baths ok")

    # Headline fuzzy alignment with buyer tags
    if buyer.tags and deal.headline:
        tags = _split_csv(buyer.tags)
        tscore = max([fuzz.partial_ratio(t.lower(), deal.headline.lower())/100.0 for t in tags] or [0.0])
        if tscore >= 0.6:
            score += 0.10 * tscore
            reasons.append(f"tag≈headline ({tscore:.2f})")

    return min(1.0, score), reasons
