"""
Negotiations router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.negotiations.schemas import NegotiationCreate, NegotiationOut
from app.negotiations.service import start_negotiation, update_negotiation

router = APIRouter(prefix="/negotiations", tags=["negotiations"])


@router.post("/", response_model=NegotiationOut)
async def create_new_negotiation(negotiation: NegotiationCreate, db: Session = Depends(get_db)):
    return start_negotiation(db=db, negotiation=negotiation)


@router.put("/{negotiation_id}", response_model=NegotiationOut)
async def update_existing_negotiation(negotiation_id: int, tone_score: float, sentiment_score: float, stage: str, db: Session = Depends(get_db)):
    updated = update_negotiation(db=db, negotiation_id=negotiation_id, tone_score=tone_score, sentiment_score=sentiment_score, stage=stage)
    if not updated:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return updated
