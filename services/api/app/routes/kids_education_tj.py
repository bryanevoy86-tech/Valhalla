"""
PACK TJ: Kids Education & Development Router
Prefix: /kids
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.kids_education_tj import (
    ChildProfileCreate,
    ChildProfileOut,
    LearningPlanCreate,
    LearningPlanOut,
    EducationLogCreate,
    EducationLogOut,
    ChildWeeklySummary,
)
from app.services.kids_education_tj import (
    create_child,
    list_children,
    create_learning_plan,
    create_education_log,
    get_child_weekly_summary,
)

router = APIRouter(prefix="/kids", tags=["Kids Education"])


@router.post("/children", response_model=ChildProfileOut)
def create_child_endpoint(
    payload: ChildProfileCreate,
    db: Session = Depends(get_db),
):
    """Create a new child profile."""
    return create_child(db, payload)


@router.get("/children", response_model=List[ChildProfileOut])
def list_children_endpoint(
    db: Session = Depends(get_db),
):
    """List all child profiles."""
    return list_children(db)


@router.post("/learning-plans", response_model=LearningPlanOut)
def create_learning_plan_endpoint(
    payload: LearningPlanCreate,
    db: Session = Depends(get_db),
):
    """Create a learning plan for a child."""
    plan = create_learning_plan(db, payload)
    if not plan:
        raise HTTPException(status_code=404, detail="Child not found")
    return plan


@router.post("/logs", response_model=EducationLogOut)
def create_education_log_endpoint(
    payload: EducationLogCreate,
    db: Session = Depends(get_db),
):
    """Create an education log entry for a child."""
    log = create_education_log(db, payload)
    if not log:
        raise HTTPException(status_code=404, detail="Child not found")
    return log


@router.get("/children/{child_id}/weekly-summary", response_model=ChildWeeklySummary)
def get_child_weekly_summary_endpoint(
    child_id: int,
    week_of: datetime = Query(..., description="Start date of the week"),
    db: Session = Depends(get_db),
):
    """Get weekly summary for a child."""
    summary = get_child_weekly_summary(db, child_id, week_of)
    if not summary:
        raise HTTPException(status_code=404, detail="Child not found")
    return summary
