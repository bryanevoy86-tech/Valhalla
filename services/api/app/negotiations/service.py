"""
Negotiation service logic.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.negotiations.models import Negotiation
from app.negotiations.schemas import NegotiationCreate


def start_negotiation(db: Session, negotiation: NegotiationCreate) -> Negotiation:
    db_neg = Negotiation(
        user_id=negotiation.user_id,
        deal_id=negotiation.deal_id,
        tone_score=negotiation.tone_score,
        sentiment_score=negotiation.sentiment_score,
        negotiation_stage=negotiation.negotiation_stage or "initial",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_neg)
    db.commit()
    db.refresh(db_neg)
    return db_neg


def update_negotiation(db: Session, negotiation_id: int, tone_score: float, sentiment_score: float, stage: str) -> Negotiation | None:
    db_neg = db.query(Negotiation).filter(Negotiation.id == negotiation_id).first()
    if not db_neg:
        return None
    setattr(db_neg, "tone_score", tone_score)
    setattr(db_neg, "sentiment_score", sentiment_score)
    setattr(db_neg, "negotiation_stage", stage)
    setattr(db_neg, "updated_at", datetime.utcnow())
    db.commit()
    db.refresh(db_neg)
    return db_neg
