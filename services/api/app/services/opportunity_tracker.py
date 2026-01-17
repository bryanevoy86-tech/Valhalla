"""
PACK SK: Arbitrage / Side-Hustle Opportunity Tracker
Service functions for opportunity management and performance tracking
"""
from sqlalchemy.orm import Session
from app.models.opportunity_tracker import (
    Opportunity, OpportunityScore, OpportunityPerformance, OpportunitySummary
)
from datetime import datetime
from typing import List, Optional, Dict, Any


def create_opportunity(
    db: Session,
    opportunity_id: str,
    name: str,
    category: str,
    startup_cost: int,
    description: Optional[str] = None,
    expected_effort: Optional[float] = None,
    potential_return: Optional[int] = None,
    risk_level: Optional[str] = None,
    notes: Optional[str] = None
) -> Opportunity:
    """Create a new opportunity."""
    opp = Opportunity(
        opportunity_id=opportunity_id,
        name=name,
        category=category,
        description=description,
        startup_cost=startup_cost,
        expected_effort=expected_effort,
        potential_return=potential_return,
        risk_level=risk_level,
        notes=notes,
        status="idea"
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


def get_opportunity(db: Session, opportunity_id: int) -> Optional[Opportunity]:
    """Get an opportunity by ID."""
    return db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()


def list_opportunities(db: Session, status: Optional[str] = None, category: Optional[str] = None) -> List[Opportunity]:
    """List opportunities, optionally filtered."""
    query = db.query(Opportunity)
    if status:
        query = query.filter(Opportunity.status == status)
    if category:
        query = query.filter(Opportunity.category == category)
    return query.all()


def update_opportunity_status(db: Session, opportunity_id: int, new_status: str) -> Opportunity:
    """Update opportunity status."""
    opp = get_opportunity(db, opportunity_id)
    if opp:
        opp.status = new_status
        opp.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(opp)
    return opp


def create_opportunity_score(
    db: Session,
    score_id: str,
    opportunity_id: int,
    time_efficiency: Optional[float] = None,
    scalability: Optional[float] = None,
    difficulty: Optional[float] = None,
    personal_interest: Optional[float] = None,
    overall_score: Optional[float] = None,
    notes: Optional[str] = None
) -> OpportunityScore:
    """Create or update an opportunity score (user-provided)."""
    score = OpportunityScore(
        score_id=score_id,
        opportunity_id=opportunity_id,
        time_efficiency=time_efficiency,
        scalability=scalability,
        difficulty=difficulty,
        personal_interest=personal_interest,
        overall_score=overall_score,
        notes=notes
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def log_performance(
    db: Session,
    log_id: str,
    opportunity_id: int,
    date: datetime,
    effort_hours: Optional[float] = None,
    revenue: Optional[int] = None,
    notes: Optional[str] = None
) -> OpportunityPerformance:
    """Log performance data for an opportunity."""
    log = OpportunityPerformance(
        log_id=log_id,
        opportunity_id=opportunity_id,
        date=date,
        effort_hours=effort_hours,
        revenue=revenue,
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_performance_logs(db: Session, opportunity_id: int) -> List[OpportunityPerformance]:
    """Get all performance logs for an opportunity."""
    return db.query(OpportunityPerformance).filter(
        OpportunityPerformance.opportunity_id == opportunity_id
    ).order_by(OpportunityPerformance.date).all()


def create_opportunity_summary(
    db: Session,
    summary_id: str,
    opportunity_id: int,
    period: str,
    total_effort_hours: float,
    total_revenue: int,
    roi: Optional[float] = None,
    status_update: Optional[str] = None,
    notes: Optional[str] = None
) -> OpportunitySummary:
    """Create a summary for an opportunity."""
    summary = OpportunitySummary(
        summary_id=summary_id,
        opportunity_id=opportunity_id,
        period=period,
        total_effort_hours=total_effort_hours,
        total_revenue=total_revenue,
        roi=roi,
        status_update=status_update,
        notes=notes
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_opportunity_summary(db: Session, opportunity_id: int, period: str) -> Optional[OpportunitySummary]:
    """Get summary for a specific period."""
    return db.query(OpportunitySummary).filter(
        OpportunitySummary.opportunity_id == opportunity_id,
        OpportunitySummary.period == period
    ).first()


def calculate_opportunity_metrics(db: Session, opportunity_id: int) -> Dict[str, Any]:
    """Calculate metrics for an opportunity."""
    opp = get_opportunity(db, opportunity_id)
    if not opp:
        return {}

    logs = get_performance_logs(db, opportunity_id)
    
    total_hours = sum(log.effort_hours for log in logs if log.effort_hours)
    total_revenue = sum(log.revenue for log in logs if log.revenue)
    
    return {
        "opportunity_id": opp.opportunity_id,
        "name": opp.name,
        "startup_cost": opp.startup_cost,
        "total_hours_invested": total_hours,
        "total_revenue": total_revenue,
        "roi": (total_revenue - opp.startup_cost) / opp.startup_cost if opp.startup_cost > 0 else 0,
        "status": opp.status
    }
