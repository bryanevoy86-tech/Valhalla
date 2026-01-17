"""
PACK SK: Arbitrage/Side-Hustle Opportunity Tracker Router
FastAPI endpoints for opportunity management and performance tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.opportunity_tracker import (
    OpportunitySchema, OpportunityScoreSchema, OpportunityPerformanceSchema,
    OpportunitySummarySchema, OpportunityComparisonResponse
)
from app.services.opportunity_tracker import (
    create_opportunity, get_opportunity, list_opportunities, update_opportunity_status,
    create_opportunity_score,
    log_performance, get_performance_logs,
    create_opportunity_summary, get_opportunity_summary,
    calculate_opportunity_metrics
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.post("/", response_model=OpportunitySchema)
def create_new_opportunity(opportunity_data: dict, db: Session = Depends(get_db)):
    """Create a new opportunity."""
    return create_opportunity(db, **opportunity_data)


@router.get("/{opportunity_id}", response_model=OpportunitySchema)
def get_opp(opportunity_id: int, db: Session = Depends(get_db)):
    """Get a specific opportunity."""
    opp = get_opportunity(db, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.get("/", response_model=list[OpportunitySchema])
def list_all_opportunities(category: str = None, status: str = None, db: Session = Depends(get_db)):
    """List all opportunities with optional filters."""
    return list_opportunities(db, category=category, status=status)


@router.put("/{opportunity_id}/status", response_model=OpportunitySchema)
def update_status(opportunity_id: int, status: str, db: Session = Depends(get_db)):
    """Update opportunity status."""
    opp = update_opportunity_status(db, opportunity_id, status)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@router.post("/{opportunity_id}/score", response_model=OpportunityScoreSchema)
def add_score(opportunity_id: int, score_data: dict, db: Session = Depends(get_db)):
    """Add a score/evaluation for an opportunity."""
    score_data["opportunity_id"] = opportunity_id
    return create_opportunity_score(db, **score_data)


@router.post("/{opportunity_id}/performance", response_model=OpportunityPerformanceSchema)
def log_perf(opportunity_id: int, perf_data: dict, db: Session = Depends(get_db)):
    """Log performance metrics for an opportunity."""
    perf_data["opportunity_id"] = opportunity_id
    return log_performance(db, **perf_data)


@router.get("/{opportunity_id}/performance", response_model=list[OpportunityPerformanceSchema])
def get_perf_logs(opportunity_id: int, db: Session = Depends(get_db)):
    """Get performance logs for an opportunity."""
    return get_performance_logs(db, opportunity_id)


@router.post("/{opportunity_id}/summary", response_model=OpportunitySummarySchema)
def create_summary(opportunity_id: int, summary_data: dict, db: Session = Depends(get_db)):
    """Create a period summary for an opportunity."""
    summary_data["opportunity_id"] = opportunity_id
    return create_opportunity_summary(db, **summary_data)


@router.get("/{opportunity_id}/summary", response_model=OpportunitySummarySchema)
def get_summary(opportunity_id: int, db: Session = Depends(get_db)):
    """Get summary for an opportunity."""
    summary = get_opportunity_summary(db, opportunity_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.get("/comparison/metrics", response_model=OpportunityComparisonResponse)
def compare_opportunities(db: Session = Depends(get_db)):
    """Get comparison metrics across all opportunities."""
    opportunities = list_opportunities(db)
    metrics = [calculate_opportunity_metrics(db, opp.id) for opp in opportunities]
    return OpportunityComparisonResponse(opportunities=opportunities, metrics=metrics)
