from __future__ import annotations

from typing import Any

from app.core_gov.buyers.store import load_buyers
from app.core_gov.deals.scoring.service import score_deal

def match_buyers_to_deal(deal: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    buyers = load_buyers()

    deal_country = (deal.get("country") or "CA").upper()
    deal_state = (deal.get("province_state") or "").upper()
    strategy = (deal.get("strategy") or "wholesale").lower()
    ptype = (deal.get("property_type") or "sfh").lower()
    arv = float(deal.get("arv") or 0)
    repairs = float(deal.get("est_repairs") or 0)

    s = score_deal(deal)
    equity_pct = float(s.get("equity_pct") or 0.0)  # percent already

    scored = []
    for b in buyers:
        # country filter
        if (b.get("country") or "CA").upper() != deal_country:
            continue

        # state/province preference (if set)
        b_state = (b.get("province_state") or "").upper()
        if b_state and b_state != deal_state:
            continue

        # strategy match
        b_strats = [x.lower() for x in (b.get("strategies") or [])]
        if b_strats and strategy not in b_strats:
            continue

        # property type match
        b_ptypes = [x.lower() for x in (b.get("property_types") or [])]
        if b_ptypes and ptype not in b_ptypes:
            continue

        # filters
        min_arv = b.get("min_arv")
        max_arv = b.get("max_arv")
        if min_arv is not None and arv and arv < float(min_arv):
            continue
        if max_arv is not None and arv and arv > float(max_arv):
            continue

        max_rep = b.get("max_repairs")
        if max_rep is not None and repairs and repairs > float(max_rep):
            continue

        min_eq = b.get("min_equity_pct")
        if min_eq is not None and equity_pct < float(min_eq):
            continue

        # simple match score
        match_score = 60
        if b_state:
            match_score += 10
        if min_arv is not None or max_arv is not None:
            match_score += 5
        if max_rep is not None:
            match_score += 5
        if equity_pct >= 30:
            match_score += 10

        scored.append((match_score, b))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for ms, b in scored[:limit]:
        out.append({
            "buyer_id": b.get("id"),
            "name": b.get("name"),
            "contact": b.get("contact"),
            "country": b.get("country"),
            "province_state": b.get("province_state"),
            "strategies": b.get("strategies"),
            "property_types": b.get("property_types"),
            "match_score": ms,
            "tags": b.get("tags") or [],
        })
    return out
