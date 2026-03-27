"""
Operational Dashboard Router
Endpoints for viewing real deal pipeline state and audit timelines.
Returns data directly from database (no caching).
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.deal import Deal
from ..audit.models import AuditEvent

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ===== SCHEMAS =====

class DealPipelineItem(BaseModel):
    """Single deal in the operational pipeline."""
    deal_id: int
    title: str
    stage: str
    score: Optional[float] = 0.0
    contract_status: Optional[str] = None
    buyer_status: Optional[str] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True


class DealPipeline(BaseModel):
    """Complete operational pipeline view."""
    total_deals: int
    deals: List[DealPipelineItem]


class AuditTimelineEntry(BaseModel):
    """Single audit event in a deal's timeline."""
    timestamp: datetime
    action: str
    actor: str
    target: Optional[str] = None
    result: str
    meta: Optional[dict] = None
    
    class Config:
        from_attributes = True


class DealTimeline(BaseModel):
    """Timeline of events for a specific deal."""
    deal_id: int
    deal_title: str
    events: List[AuditTimelineEntry]


# ===== ENDPOINTS =====

@router.get("/pipeline", response_model=DealPipeline)
def get_pipeline(db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    """
    Get operational pipeline view showing all active deals and their current state.
    
    Returns:
    - total_deals: count of deals
    - deals: list of DealPipelineItem with current status
    """
    # Query all active deals from canonical Deal model
    deals = db.query(Deal).filter(Deal.status == "active").all()
    
    pipeline_items = []
    for deal in deals:
        item = DealPipelineItem(
            deal_id=deal.id,
            title=deal.title or f"Deal {deal.id}",
            stage=deal.stage or "unknown",
            score=float(deal.score) if deal.score else 0.0,
            contract_status="pending",  # TODO: Join to contracts table
            buyer_status="unmatched",   # TODO: Join to buyer_matches table
            last_updated=deal.updated_at or deal.created_at or datetime.utcnow()
        )
        pipeline_items.append(item)
    
    return DealPipeline(
        total_deals=len(pipeline_items),
        deals=pipeline_items
    )


@router.get("/deals/{deal_id}/timeline", response_model=DealTimeline)
def get_deal_timeline(
    deal_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """
    Get audit timeline for a specific deal showing all actions and stage changes.
    
    Returns ordered list of audit events by timestamp, newest first.
    """
    # Verify deal exists
    deal_brief = db.query(DealBrief).filter(DealBrief.id == deal_id).first()
    full_deal = db.query(Deal).filter(Deal.id == deal_id).first()
    
    if not deal_brief and not full_deal:
        raise HTTPException(status_code=404, detail=f"deal {deal_id} not found")
    
    deal_title = (deal_brief.headline if deal_brief else None) or (
        f"Deal {deal_id}"
    )
    
    # Query all audit events for this deal
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_type == "deal", AuditEvent.entity_id == deal_id)
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
    
    timeline_entries = [
        AuditTimelineEntry(
            timestamp=event.created_at,
            action=event.action,
            actor=event.actor,
            target=event.target,
            result=event.result,
            meta=event.meta
        )
        for event in events
    ]
    
    return DealTimeline(
        deal_id=deal_id,
        deal_title=deal_title,
        events=timeline_entries
    )
