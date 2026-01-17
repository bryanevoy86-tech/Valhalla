"""
PACK SL: Personal Master Dashboard
Service functions for life operations, routines, goals, and family tracking
"""
from sqlalchemy.orm import Session
from app.models.personal_dashboard import (
    FocusArea, PersonalRoutine, RoutineCompletion, FamilySnapshot,
    LifeDashboard, PersonalGoal, MoodLog
)
from datetime import datetime
from typing import List, Optional, Dict, Any


def create_focus_area(
    db: Session,
    area_id: str,
    name: str,
    category: str,
    priority_level: int = 5,
    notes: Optional[str] = None
) -> FocusArea:
    """Create a life focus area."""
    area = FocusArea(
        area_id=area_id,
        name=name,
        category=category,
        priority_level=priority_level,
        notes=notes
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def list_focus_areas(db: Session, category: Optional[str] = None) -> List[FocusArea]:
    """List all focus areas."""
    query = db.query(FocusArea)
    if category:
        query = query.filter(FocusArea.category == category)
    return query.order_by(FocusArea.priority_level.desc()).all()


def create_personal_routine(
    db: Session,
    routine_id: str,
    name: str,
    frequency: str,
    focus_area_id: Optional[int] = None,
    description: Optional[str] = None,
    notes: Optional[str] = None
) -> PersonalRoutine:
    """Create a personal routine."""
    routine = PersonalRoutine(
        routine_id=routine_id,
        focus_area_id=focus_area_id,
        name=name,
        description=description,
        frequency=frequency,
        notes=notes,
        status="active"
    )
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return routine


def list_active_routines(db: Session) -> List[PersonalRoutine]:
    """List all active routines."""
    return db.query(PersonalRoutine).filter(PersonalRoutine.status == "active").all()


def log_routine_completion(
    db: Session,
    completion_id: str,
    routine_id: int,
    date: datetime,
    completed: int = 1,
    notes: Optional[str] = None
) -> RoutineCompletion:
    """Log routine completion."""
    completion = RoutineCompletion(
        completion_id=completion_id,
        routine_id=routine_id,
        date=date,
        completed=completed,
        notes=notes
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion


def get_routine_completion_rate(db: Session, routine_id: int, days: int = 30) -> float:
    """Calculate completion rate for a routine over last N days."""
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    completions = db.query(RoutineCompletion).filter(
        RoutineCompletion.routine_id == routine_id,
        RoutineCompletion.date >= cutoff
    ).all()
    
    if not completions:
        return 0.0
    
    completed = sum(c.completed for c in completions)
    return (completed / len(completions)) * 100 if completions else 0


def create_family_snapshot(
    db: Session,
    snapshot_id: str,
    date: datetime,
    kids_notes: Optional[List[Dict[str, Any]]] = None,
    partner_notes: Optional[str] = None,
    home_operations: Optional[str] = None,
    highlights: Optional[List[str]] = None
) -> FamilySnapshot:
    """Create a family snapshot."""
    snapshot = FamilySnapshot(
        snapshot_id=snapshot_id,
        date=date,
        kids_notes=kids_notes,
        partner_notes=partner_notes,
        home_operations=home_operations,
        highlights=highlights
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_life_dashboard(
    db: Session,
    dashboard_id: str,
    week_of: datetime,
    wins: Optional[List[str]] = None,
    challenges: Optional[List[str]] = None,
    habits_tracked: Optional[List[Dict[str, Any]]] = None,
    upcoming_priorities: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> LifeDashboard:
    """Create a weekly life dashboard."""
    dashboard = LifeDashboard(
        dashboard_id=dashboard_id,
        week_of=week_of,
        wins=wins,
        challenges=challenges,
        habits_tracked=habits_tracked,
        upcoming_priorities=upcoming_priorities,
        notes=notes
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard


def create_personal_goal(
    db: Session,
    goal_id: str,
    name: str,
    category: str,
    description: Optional[str] = None,
    deadline: Optional[datetime] = None,
    progress_percent: int = 0,
    notes: Optional[str] = None
) -> PersonalGoal:
    """Create a personal goal."""
    goal = PersonalGoal(
        goal_id=goal_id,
        name=name,
        description=description,
        category=category,
        deadline=deadline,
        progress_percent=progress_percent,
        notes=notes,
        status="active"
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal_progress(db: Session, goal_id: int, progress_percent: int) -> PersonalGoal:
    """Update goal progress."""
    goal = db.query(PersonalGoal).filter(PersonalGoal.id == goal_id).first()
    if goal:
        goal.progress_percent = min(100, max(0, progress_percent))
        if progress_percent >= 100:
            goal.status = "completed"
        goal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(goal)
    return goal


def list_active_goals(db: Session) -> List[PersonalGoal]:
    """List all active goals."""
    return db.query(PersonalGoal).filter(PersonalGoal.status == "active").all()


def log_mood(
    db: Session,
    log_id: str,
    date: datetime,
    mood: str,
    energy_level: Optional[int] = None,
    notes: Optional[str] = None
) -> MoodLog:
    """Log mood entry."""
    mood_log = MoodLog(
        log_id=log_id,
        date=date,
        mood=mood,
        energy_level=energy_level,
        notes=notes
    )
    db.add(mood_log)
    db.commit()
    db.refresh(mood_log)
    return mood_log


def get_mood_logs(db: Session, days: int = 30) -> List[MoodLog]:
    """Get mood logs for last N days."""
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    return db.query(MoodLog).filter(MoodLog.date >= cutoff).order_by(MoodLog.date.desc()).all()


def calculate_life_metrics(db: Session) -> Dict[str, Any]:
    """Calculate life operations metrics."""
    focus_areas = db.query(FocusArea).count()
    active_routines = db.query(PersonalRoutine).filter(PersonalRoutine.status == "active").count()
    active_goals = db.query(PersonalGoal).filter(PersonalGoal.status == "active").count()
    completed_goals = db.query(PersonalGoal).filter(PersonalGoal.status == "completed").count()
    
    recent_moods = get_mood_logs(db, 7)
    avg_energy = sum(m.energy_level for m in recent_moods if m.energy_level) / len(recent_moods) if recent_moods else 0
    
    return {
        "focus_areas": focus_areas,
        "active_routines": active_routines,
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "average_energy_level": avg_energy
    }
