from __future__ import annotations

from typing import Any, Dict

def score_deal(deal: dict[str, Any]) -> dict[str, Any]:
    arv = float(deal.get("arv") or 0)
    ask = float(deal.get("asking_price") or 0)
    rep = float(deal.get("est_repairs") or 0)

    # basic guards
    flags = []
    if arv <= 0:
        flags.append("missing_arv")
    if ask <= 0:
        flags.append("missing_asking")
    if rep < 0:
        flags.append("repairs_negative")

    motivation = (deal.get("seller_motivation") or "unknown").lower()
    stage = (deal.get("stage") or "new").lower()
    strategy = (deal.get("strategy") or "wholesale").lower()

    # equity proxy (very rough): (arv - ask)/arv
    equity_pct = 0.0
    if arv > 0 and ask > 0:
        equity_pct = max(0.0, (arv - ask) / arv)

    # MAO heuristic by strategy
    if strategy == "wholesale":
        mao_suggested = max(0.0, (arv * 0.70) - rep)
    elif strategy == "flip":
        mao_suggested = max(0.0, (arv * 0.75) - rep)
    elif strategy in ("brrrr", "rental"):
        mao_suggested = max(0.0, (arv * 0.80) - rep)
    else:
        mao_suggested = max(0.0, (arv * 0.70) - rep)

    # scoring bands 0-100
    score = 50

    # motivation
    if motivation == "high":
        score += 15
    elif motivation == "medium":
        score += 7
    elif motivation == "low":
        score -= 5

    # equity
    if equity_pct >= 0.35:
        score += 20
    elif equity_pct >= 0.25:
        score += 12
    elif equity_pct >= 0.15:
        score += 5
    else:
        score -= 8
        flags.append("low_equity")

    # repairs proportion
    if arv > 0:
        rep_ratio = rep / arv
        if rep_ratio >= 0.25:
            flags.append("heavy_repairs")
            score -= 8
        elif rep_ratio >= 0.15:
            score -= 4

    # stage
    if stage in ("qualified", "offer_sent", "negotiating"):
        score += 5

    # clamp
    score = max(0, min(100, score))

    return {
        "score": score,
        "equity_pct": round(equity_pct * 100, 1),
        "mao_suggested": round(mao_suggested, 2),
        "flags": flags,
    }
