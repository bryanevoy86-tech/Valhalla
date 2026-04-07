# services/api/app/services/pro_handoff_engine.py

from __future__ import annotations

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.pro_scorecard import Professional, Scorecard


def generate_handoff_packet(
    db: Session,
    professional_id: int,
    deal_id: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a professional handoff packet for escalation to human professionals.
    
    Includes:
    - Professional details
    - Scorecard (if available)
    - Deal summary (if deal_id provided)
    - Risk summary
    - Tasks outstanding
    - Documents needed
    """
    
    # Get professional
    pro = db.query(Professional).filter(Professional.id == professional_id).first()
    if not pro:
        raise ValueError(f"Professional {professional_id} not found")
    
    # Get scorecard
    score = db.query(Scorecard).filter(Scorecard.professional_id == professional_id).first()
    
    packet = {
        "handoff_timestamp": datetime.utcnow().isoformat(),
        "professional": {
            "id": pro.id,
            "name": pro.name,
            "role": pro.role,
            "organization": pro.organization,
        },
        "scorecard": None,
        "deal_summary": None,
        "risk_summary": None,
        "tasks_outstanding": [],
        "documents_needed": [],
        "context": context or {},
    }
    
    # Add scorecard if available
    if score:
        packet["scorecard"] = {
            "overall_score": score.overall_score,
            "reliability_score": score.reliability_score,
            "communication_score": score.communication_score,
            "quality_score": score.quality_score,
            "updated_at": score.updated_at.isoformat() if score.updated_at else None,
        }
    
    # Add deal summary if deal_id provided
    if deal_id:
        packet["deal_summary"] = _summarize_deal(db, deal_id)
        packet["risk_summary"] = _summarize_risks(db, deal_id)
        packet["tasks_outstanding"] = _get_outstanding_tasks(db, deal_id)
        packet["documents_needed"] = _get_required_documents(db, deal_id)
    
    return packet


def _summarize_deal(db: Session, deal_id: int) -> Dict[str, Any]:
    """Generate deal summary (placeholder - integrate with actual deal model)."""
    return {
        "deal_id": deal_id,
        "status": "pending_review",
        "summary": "Deal summary placeholder - integrate with actual deal model",
    }


def _summarize_risks(db: Session, deal_id: int) -> Dict[str, Any]:
    """Generate risk summary (placeholder - integrate with risk engine)."""
    return {
        "risk_level": "moderate",
        "key_risks": [
            "Placeholder risk 1",
            "Placeholder risk 2",
        ],
        "mitigation_required": True,
    }


def _get_outstanding_tasks(db: Session, deal_id: int) -> list:
    """Get outstanding tasks for deal (placeholder)."""
    return [
        {"task": "Review contract terms", "priority": "high"},
        {"task": "Verify property title", "priority": "medium"},
    ]


def _get_required_documents(db: Session, deal_id: int) -> list:
    """Get required documents for deal (placeholder)."""
    return [
        {"document": "Purchase agreement", "status": "pending"},
        {"document": "Title report", "status": "received"},
    ]
