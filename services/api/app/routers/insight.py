"""
PACK CI4: Insight Synthesizer Router
Prefix: /intelligence/insights
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.insight import InsightIn, InsightOut, InsightList
from app.services.insight import create_insight, list_insights

router = APIRouter(prefix="/intelligence/insights", tags=["Intelligence", "Insights"])


@router.post("/", response_model=InsightOut)
def create_insight_endpoint(
    payload: InsightIn,
    db: Session = Depends(get_db),
):
    return create_insight(db, payload)


@router.get("/", response_model=InsightList)
def list_insights_endpoint(
    category: str | None = Query(None),
    min_importance: int = Query(1, ge=1, le=10),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    items = list_insights(db, category=category, min_importance=min_importance, limit=limit)
    return InsightList(total=len(items), items=items)
