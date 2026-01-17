from __future__ import annotations

from collections import Counter
from typing import Any

from app.core_gov.deals.store import load_deals
from app.core_gov.deals.scoring.service import score_deal
from app.core_gov.deals.next_action.service import next_action_for_deal

def deals_summary(limit_scan: int = 3000, top_n: int = 15) -> dict[str, Any]:
    items = load_deals()
    items = items[-limit_scan:]

    by_stage = Counter((d.get("stage") or "unknown") for d in items)
    by_source = Counter((d.get("lead_source") or "unknown") for d in items)
    by_country = Counter((d.get("country") or "unknown") for d in items)

    # top scored
    scored = []
    for d in items[-800:]:  # keep light
        s = score_deal(d)
        scored.append((s["score"], d, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    top_scored = [{
        "id": d.get("id"),
        "country": d.get("country"),
        "province_state": d.get("province_state"),
        "city": d.get("city"),
        "strategy": d.get("strategy"),
        "stage": d.get("stage"),
        "lead_source": d.get("lead_source"),
        "score": s["score"],
        "equity_pct": s["equity_pct"],
        "mao_suggested": s["mao_suggested"],
        "flags": s["flags"],
    } for (score, d, s) in scored[:top_n]]

    # next actions (based on stage + band)
    actions = []
    for d in top_scored:
        # need full deal record for next_action
        full = next(x for x in items if x.get("id") == d["id"])
        nxt = next_action_for_deal(full)
        actions.append({"deal_id": d["id"], "priority": nxt["priority"], "action": nxt["action"], "why": nxt["why"], "band": nxt["band"]})

    return {
        "counts": {
            "total": len(items),
            "by_stage": dict(by_stage),
            "by_source": dict(by_source),
            "by_country": dict(by_country),
        },
        "top_scored": top_scored,
        "next_actions": actions,
    }
