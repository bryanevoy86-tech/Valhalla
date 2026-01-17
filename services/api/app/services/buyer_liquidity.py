from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.models.buyer_liquidity import BuyerLiquidityNode, BuyerFeedbackEvent
from app.services.kpi import emit_kpi


def _get_or_create_node(db: Session, province: str, market: str, property_type: str) -> BuyerLiquidityNode:
    province = province.strip().upper()
    market = (market or "ALL").strip().upper()
    property_type = (property_type or "SFR").strip().upper()

    row = db.query(BuyerLiquidityNode).filter(
        BuyerLiquidityNode.province == province,
        BuyerLiquidityNode.market == market,
        BuyerLiquidityNode.property_type == property_type
    ).first()
    if row:
        return row
    row = BuyerLiquidityNode(province=province, market=market, property_type=property_type)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def record_feedback(db: Session, province: str, market: str, property_type: str, event: str, buyer_id: str | None, correlation_id: str | None, detail: str | None):
    node = _get_or_create_node(db, province, market, property_type)
    ev = BuyerFeedbackEvent(
        buyer_id=buyer_id,
        province=node.province,
        market=node.market,
        property_type=node.property_type,
        event=event.strip().upper(),
        correlation_id=correlation_id,
        detail=detail
    )
    db.add(ev)

    # Update aggregates simply (you can refine later)
    if ev.event == "RESPONDED":
        node.avg_response_rate = min(1.0, node.avg_response_rate + 0.01)
        node.active_buyer_count += 1
    elif ev.event == "NO_RESPONSE":
        node.avg_response_rate = max(0.0, node.avg_response_rate - 0.01)
    elif ev.event == "BOUGHT":
        node.avg_close_rate = min(1.0, node.avg_close_rate + 0.01)
    elif ev.event == "PASSED":
        node.avg_close_rate = max(0.0, node.avg_close_rate - 0.01)

    node.updated_at = datetime.utcnow()
    db.add(node)
    db.commit()

    emit_kpi(db, "BUYER_MATCH", "buyer_feedback", success=True, correlation_id=correlation_id, detail={"event": ev.event, "province": node.province, "market": node.market, "property_type": node.property_type})


def liquidity_score(db: Session, province: str, market: str, property_type: str) -> Dict[str, Any]:
    node = _get_or_create_node(db, province, market, property_type)
    # Simple weighted score; refine later.
    score = (node.active_buyer_count * 0.5) + (node.avg_response_rate * 50.0) + (node.avg_close_rate * 50.0)
    return {
        "province": node.province,
        "market": node.market,
        "property_type": node.property_type,
        "buyer_count": node.buyer_count,
        "active_buyer_count": node.active_buyer_count,
        "avg_response_rate": node.avg_response_rate,
        "avg_close_rate": node.avg_close_rate,
        "score": score,
        "updated_at": node.updated_at,
    }
