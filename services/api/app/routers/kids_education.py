"""
PACK SM: Kids Education & Development Engine Router
FastAPI endpoints for learning plans and education tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.kids_education import (
    ChildProfileSchema, LearningPlanSchema, EducationLogSchema,
    ChildSummarySchema, ChildEducationResponse
)
from app.services.kids_education import (
    create_child_profile, list_children, create_learning_plan,
    list_active_plans, log_education_activity, get_education_logs,
    create_child_summary, get_child_summary, calculate_education_metrics
)

router = APIRouter(prefix="/kids", tags=["kids-education"])


@router.post("/profiles", response_model=ChildProfileSchema)
def add_child_profile(profile_data: dict, db: Session = Depends(get_db)):
    """Create a child profile."""
    return create_child_profile(db, **profile_data)


@router.get("/profiles", response_model=list[ChildProfileSchema])
def list_all_children(db: Session = Depends(get_db)):
    """List all children."""
    return list_children(db)


@router.post("/learning-plans", response_model=LearningPlanSchema)
def add_learning_plan(plan_data: dict, db: Session = Depends(get_db)):
    """Create a learning plan."""
    return create_learning_plan(db, **plan_data)


@router.get("/learning-plans", response_model=list[LearningPlanSchema])
def list_learning_plans(child_id: int = None, db: Session = Depends(get_db)):
    """List active learning plans."""
    return list_active_plans(db, child_id=child_id)


@router.post("/education-logs", response_model=EducationLogSchema)
def add_education_log(log_data: dict, db: Session = Depends(get_db)):
    """Log education activity."""
    return log_education_activity(db, **log_data)


@router.get("/education-logs/{child_id}", response_model=list[EducationLogSchema])
def get_recent_logs(child_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Get recent education logs for a child."""
    return get_education_logs(db, child_id, days=days)


@router.post("/summaries", response_model=ChildSummarySchema)
def add_child_summary(summary_data: dict, db: Session = Depends(get_db)):
    """Create a weekly education summary."""
    return create_child_summary(db, **summary_data)


@router.get("/summaries/{child_id}", response_model=ChildSummarySchema)
def get_summary(child_id: int, db: Session = Depends(get_db)):
    """Get most recent summary for a child."""
    summary = get_child_summary(db, child_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.get("/metrics/{child_id}", response_model=ChildEducationResponse)
def get_metrics(child_id: int, db: Session = Depends(get_db)):
    """Get education metrics for a child."""
    metrics = calculate_education_metrics(db, child_id)
    return ChildEducationResponse(
        total_children=1,
        active_plans=metrics["active_plans"],
        this_week_logs=metrics["logs_this_week"],
        recent_highlights=metrics["recent_highlights"]
    )
