"""
Router for Automated Deal Analyzer (Pack 34).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deal_analyzer.schemas import DealAnalysisCreate, DealAnalysisOut
from app.deal_analyzer.service import (
    analyze_and_create_deal,
    get_all_analyses,
    get_analysis_by_id,
    get_profitable_deals,
    get_deals_by_recommendation,
)

router = APIRouter(prefix="/deal-analyzer", tags=["deal-analyzer"])


@router.post("/analyze", response_model=DealAnalysisOut, status_code=201)
async def analyze_deal(deal: DealAnalysisCreate, db: Session = Depends(get_db)):
    """
    Analyze a real estate deal using AI-driven metrics.
    Calculates ROI, profitability, risk score, and provides recommendation.
    """
    return analyze_and_create_deal(db=db, deal=deal)


@router.get("/", response_model=List[DealAnalysisOut])
async def list_analyses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    recommendation: str | None = Query(None, description="Filter by AI recommendation (pass, review, reject)"),
    min_roi: float | None = Query(None, ge=0.0, description="Minimum ROI percentage for profitable deals"),
    db: Session = Depends(get_db),
):
    """List all deal analyses with optional filtering."""
    if recommendation:
        return get_deals_by_recommendation(db=db, recommendation=recommendation)
    elif min_roi is not None:
        return get_profitable_deals(db=db, min_roi=min_roi)
    return get_all_analyses(db=db, skip=skip, limit=limit)


@router.get("/{analysis_id}", response_model=DealAnalysisOut)
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Get a specific deal analysis by ID."""
    analysis = get_analysis_by_id(db=db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Deal analysis not found")
    return analysis


@router.get("/profitable/top", response_model=List[DealAnalysisOut])
async def get_top_profitable_deals(
    min_roi: float = Query(20.0, ge=0.0, description="Minimum ROI percentage"),
    db: Session = Depends(get_db),
):
    """Get top profitable deals sorted by ROI."""
    return get_profitable_deals(db=db, min_roi=min_roi)
