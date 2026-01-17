"""
PACK CI1: Decision Recommendation Engine Service
"""

from typing import List
from sqlalchemy.orm import Session

from app.models.decision_recommendation import (
    DecisionContextSnapshot,
    DecisionRecommendation,
)
from app.schemas.decision_recommendation import (
    DecisionContextIn,
    DecisionRecommendationIn,
)


def create_context(db: Session, payload: DecisionContextIn) -> DecisionContextSnapshot:
    obj = DecisionContextSnapshot(
        source=payload.source,
        mode=payload.mode,
        context_data=payload.context_data,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _compute_priority_rank(
    leverage_score: float,
    risk_score: float,
    urgency_score: float,
    alignment_score: float,
) -> int:
    """
    Simple heuristic for now:
    - Favors high leverage, high urgency, high alignment
    - Penalizes high risk
    You can tune these weights later.
    """
    score = (
        (leverage_score * 0.35)
        + (urgency_score * 0.30)
        + (alignment_score * 0.25)
        - (risk_score * 0.20)
    )
    rank = int(1000 - (score * 10))
    if rank < 1:
        rank = 1
    return rank


def generate_recommendations(
    db: Session,
    context: DecisionContextSnapshot,
    drafts: List[DecisionRecommendationIn],
) -> List[DecisionRecommendation]:
    """
    Takes a context + list of draft recommendations with raw scores,
    computes priority_rank and stores them.
    """
    created: List[DecisionRecommendation] = []

    for draft in drafts:
        rank = _compute_priority_rank(
            leverage_score=draft.leverage_score,
            risk_score=draft.risk_score,
            urgency_score=draft.urgency_score,
            alignment_score=draft.alignment_score,
        )
        rec = DecisionRecommendation(
            context_id=context.id,
            title=draft.title,
            description=draft.description,
            category=draft.category,
            leverage_score=draft.leverage_score,
            risk_score=draft.risk_score,
            urgency_score=draft.urgency_score,
            alignment_score=draft.alignment_score,
            priority_rank=rank,
            recommended=True,
            reasoning=draft.reasoning,
        )
        db.add(rec)
        created.append(rec)

    db.commit()
    for rec in created:
        db.refresh(rec)

    created.sort(key=lambda r: r.priority_rank)
    return created


def get_recommendations_for_context(
    db: Session,
    context_id: int,
) -> List[DecisionRecommendation]:
    return (
        db.query(DecisionRecommendation)
        .filter(DecisionRecommendation.context_id == context_id)
        .order_by(DecisionRecommendation.priority_rank.asc())
        .all()
    )
