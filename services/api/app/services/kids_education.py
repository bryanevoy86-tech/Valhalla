"""
PACK SM: Kids Education & Development Engine
Service functions for learning plans and education tracking
"""
from sqlalchemy.orm import Session
from app.models.kids_education import KidsEducationSMChildProfile, LearningPlan, EducationLog, ChildSummary
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


def create_child_profile(
    db: Session,
    child_id: str,
    name: str,
    age: int,
    interests: Optional[List[str]] = None,
    skill_levels: Optional[Dict[str, str]] = None,
    notes: Optional[str] = None
) -> KidsEducationSMChildProfile:
    """Create a child profile."""
    child = KidsEducationSMChildProfile(
        child_id=child_id,
        name=name,
        age=age,
        interests=interests,
        skill_levels=skill_levels,
        notes=notes
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child


def list_children(db: Session) -> List[KidsEducationSMChildProfile]:
    """List all children."""
    return db.query(KidsEducationSMChildProfile).order_by(KidsEducationSMChildProfile.age).all()


def create_learning_plan(
    db: Session,
    plan_id: str,
    child_id: int,
    timeframe: str,
    goals: Optional[List[Dict[str, str]]] = None,
    activities: Optional[List[Dict[str, Any]]] = None,
    parent_notes: Optional[str] = None
) -> LearningPlan:
    """Create a learning plan for a child."""
    plan = LearningPlan(
        plan_id=plan_id,
        child_id=child_id,
        timeframe=timeframe,
        goals=goals,
        activities=activities,
        parent_notes=parent_notes,
        status="active"
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def list_active_plans(db: Session, child_id: Optional[int] = None) -> List[LearningPlan]:
    """List active learning plans."""
    query = db.query(LearningPlan).filter(LearningPlan.status == "active")
    if child_id:
        query = query.filter(LearningPlan.child_id == child_id)
    return query.all()


def log_education_activity(
    db: Session,
    log_id: str,
    child_id: int,
    date: datetime,
    completed_activities: Optional[List[str]] = None,
    highlights: Optional[List[str]] = None,
    parent_notes: Optional[str] = None
) -> EducationLog:
    """Log daily education activities."""
    log = EducationLog(
        log_id=log_id,
        child_id=child_id,
        date=date,
        completed_activities=completed_activities,
        highlights=highlights,
        parent_notes=parent_notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_education_logs(db: Session, child_id: int, days: int = 7) -> List[EducationLog]:
    """Get recent education logs for a child."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return db.query(EducationLog).filter(
        EducationLog.child_id == child_id,
        EducationLog.date >= cutoff
    ).order_by(EducationLog.date.desc()).all()


def create_child_summary(
    db: Session,
    summary_id: str,
    child_id: int,
    week_of: datetime,
    completed_goals: Optional[List[str]] = None,
    fun_moments: Optional[List[str]] = None,
    growth_notes: Optional[str] = None,
    next_week_focus: Optional[List[str]] = None
) -> ChildSummary:
    """Create a weekly education summary."""
    summary = ChildSummary(
        summary_id=summary_id,
        child_id=child_id,
        week_of=week_of,
        completed_goals=completed_goals,
        fun_moments=fun_moments,
        growth_notes=growth_notes,
        next_week_focus=next_week_focus
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_child_summary(db: Session, child_id: int, week_of: Optional[datetime] = None) -> Optional[ChildSummary]:
    """Get child summary for a specific week."""
    query = db.query(ChildSummary).filter(ChildSummary.child_id == child_id)
    if week_of:
        query = query.filter(ChildSummary.week_of == week_of)
    return query.order_by(ChildSummary.week_of.desc()).first()


def calculate_education_metrics(db: Session, child_id: int) -> Dict[str, Any]:
    """Calculate education metrics for a child."""
    plans = db.query(LearningPlan).filter(
        LearningPlan.child_id == child_id,
        LearningPlan.status == "active"
    ).count()
    
    logs_this_week = db.query(EducationLog).filter(
        EducationLog.child_id == child_id,
        EducationLog.date >= datetime.utcnow() - timedelta(days=7)
    ).count()
    
    total_highlights = 0
    all_highlights = []
    logs = db.query(EducationLog).filter(EducationLog.child_id == child_id).all()
    for log in logs:
        if log.highlights:
            total_highlights += len(log.highlights)
            all_highlights.extend(log.highlights[-3:])  # Keep last 3 from each log
    
    return {
        "active_plans": plans,
        "logs_this_week": logs_this_week,
        "total_highlights": total_highlights,
        "recent_highlights": all_highlights[:5]
    }
