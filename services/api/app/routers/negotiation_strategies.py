"""
Negotiation Strategies router (Pack 30).
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.negotiation_strategies.schemas import StrategyCreate, StrategyOut, StrategySuggestionRequest
from app.negotiation_strategies.service import add_strategy, list_strategies, suggest_strategies

router = APIRouter(prefix="/negotiation-strategies", tags=["negotiation-strategies"])


@router.post("/", response_model=StrategyOut)
async def create_strategy(data: StrategyCreate, db: Session = Depends(get_db)):
    return add_strategy(db, data)


@router.get("/", response_model=List[StrategyOut])
async def get_strategies(db: Session = Depends(get_db)):
    return list_strategies(db)


@router.post("/suggest", response_model=List[StrategyOut])
async def suggest_for_context(req: StrategySuggestionRequest, db: Session = Depends(get_db)):
    return suggest_strategies(db, req.tone_score, req.sentiment_score)
