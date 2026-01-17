"""
Adaptive Negotiator service: create/list strategies and suggest.
"""
from sqlalchemy.orm import Session
from app.negotiation_strategies.models import NegotiationStrategy
from app.negotiation_strategies.schemas import StrategyCreate


def add_strategy(db: Session, data: StrategyCreate) -> NegotiationStrategy:
    obj = NegotiationStrategy(name=data.name, description=data.description, category=data.category)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_strategies(db: Session) -> list[NegotiationStrategy]:
    return db.query(NegotiationStrategy).order_by(NegotiationStrategy.id.desc()).all()


def suggest_strategies(db: Session, tone_score: float, sentiment_score: float) -> list[NegotiationStrategy]:
    # Simple heuristic: if sentiment low -> empathy/rapport; if tone high -> mirroring/labeling; else framing/default
    q = db.query(NegotiationStrategy)
    suggestions: list[NegotiationStrategy] = []
    if sentiment_score < -0.2:
        suggestions = q.filter(NegotiationStrategy.category.in_(["empathy", "rapport"]))[:5]
    elif tone_score > 0.5:
        suggestions = q.filter(NegotiationStrategy.category.in_(["mirroring", "labeling"]))[:5]
    else:
        suggestions = q.filter(NegotiationStrategy.category.in_(["framing", "collaborative"]))[:5]
    if not suggestions:
        suggestions = q.limit(5).all()
    return suggestions
