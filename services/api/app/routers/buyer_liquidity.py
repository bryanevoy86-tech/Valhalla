from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.buyer_liquidity import BuyerLiquidityNode
from app.services.buyer_liquidity import record_feedback, liquidity_score

router = APIRouter(prefix="/buyers/liquidity", tags=["Buyers", "Liquidity"])


@router.get("/nodes")
def nodes(db: Session = Depends(get_db)):
    rows = db.query(BuyerLiquidityNode).order_by(BuyerLiquidityNode.province.asc(), BuyerLiquidityNode.market.asc()).all()
    return {"ok": True, "nodes": [{
        "province": r.province, "market": r.market, "property_type": r.property_type,
        "buyer_count": r.buyer_count, "active_buyer_count": r.active_buyer_count,
        "avg_response_rate": r.avg_response_rate, "avg_close_rate": r.avg_close_rate, "updated_at": r.updated_at
    } for r in rows]}


@router.get("/score")
def score(province: str, market: str = "ALL", property_type: str = "SFR", db: Session = Depends(get_db)):
    return {"ok": True, "score": liquidity_score(db, province, market, property_type)}


@router.post("/feedback")
def feedback(province: str, market: str = "ALL", property_type: str = "SFR", event: str = "RESPONDED",
             buyer_id: str | None = None, correlation_id: str | None = None, detail: str | None = None,
             db: Session = Depends(get_db)):
    record_feedback(db, province, market, property_type, event, buyer_id, correlation_id, detail)
    return {"ok": True}
