"""
Match jobs for sweeping top buyer-deal matches.
"""

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.match import Buyer, DealBrief
from app.core.matcher import score_buyer_vs_deal

def sweep_top_matches(limit: int = 10) -> dict:
    """Compute top matches for all active deals vs active buyers (no persistence, returns counts)."""
    db: Session = SessionLocal()
    try:
        deals = db.query(DealBrief).filter(DealBrief.status == "active").all()
        buyers = db.query(Buyer).filter(Buyer.active.is_(True)).all()
        count = 0
        for d in deals:
            ranked = []
            for b in buyers:
                s, _ = score_buyer_vs_deal(b, d)
                ranked.append((s, b.id))
            ranked.sort(reverse=True, key=lambda t: t[0])
            top = [bid for s, bid in ranked[:limit] if s >= 0.4]
            if top:
                count += 1
        return {
            "ok": True,
            "deals_evaluated": len(deals),
            "buyers_evaluated": len(buyers),
            "deals_with_top_hits": count
        }
    finally:
        db.close()
