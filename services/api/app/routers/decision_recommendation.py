"""
PACK CI1: Decision Recommendation Engine Router
Prefix: /intelligence/decisions
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.decision_recommendation import DecisionContextSnapshot
from app.schemas.decision_recommendation import (
    DecisionContextIn,
    DecisionContextOut,
    DecisionRecommendationIn,
    DecisionRecommendationOut,
    DecisionRecommendationList,
)
from app.services.decision_recommendation import (
    create_context,
    generate_recommendations,
    get_recommendations_for_context,
)

router = APIRouter(prefix="/intelligence/decisions", tags=["Intelligence", "Decisions"])


class DecisionGenerationRequest(DecisionContextIn):
    recommendations: List[DecisionRecommendationIn]


@router.post("/generate", response_model=DecisionRecommendationList)
def generate_decisions_endpoint(
    payload: DecisionGenerationRequest,
    db: Session = Depends(get_db),
):
    """
    Given a context (mode + data) and a list of candidate moves with scores,
    compute priority ranks and return a sorted list.
    """
    ctx = create_context(
        db,
        DecisionContextIn(
            source=payload.source,
            mode=payload.mode,
            context_data=payload.context_data,
        ),
    )
    recs = generate_recommendations(db, ctx, payload.recommendations)

    return DecisionRecommendationList(
        context=DecisionContextOut.model_validate(ctx),
        items=[DecisionRecommendationOut.model_validate(r) for r in recs],
    )


@router.get("/{context_id}", response_model=DecisionRecommendationList)
def get_decisions_for_context_endpoint(
    context_id: int,
    db: Session = Depends(get_db),
):
    ctx = db.query(DecisionContextSnapshot).filter(DecisionContextSnapshot.id == context_id).first()
    if not ctx:
        raise HTTPException(status_code=404, detail="Context not found")

    recs = get_recommendations_for_context(db, context_id)
    return DecisionRecommendationList(
        context=DecisionContextOut.model_validate(ctx),
        items=[DecisionRecommendationOut.model_validate(r) for r in recs],
    )
