"""
PACK SL: Personal Master Dashboard Router
FastAPI endpoints for life operations, routines, goals, and family tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.personal_dashboard import (
    FocusAreaSchema, PersonalRoutineSchema, RoutineCompletionSchema,
    FamilySnapshotSchema, LifeDashboardSchema, PersonalGoalSchema,
    MoodLogSchema, LifeOperationsResponse
)
from app.services.personal_dashboard import (
    create_focus_area, list_focus_areas,
    create_personal_routine, list_active_routines,
    log_routine_completion, get_routine_completion_rate,
    create_family_snapshot, create_life_dashboard,
    create_personal_goal, update_goal_progress, list_active_goals,
    log_mood, get_mood_logs, calculate_life_metrics
)

router = APIRouter(prefix="/life", tags=["life-operations"])


@router.post("/focus-areas", response_model=FocusAreaSchema)
def add_focus_area(area_data: dict, db: Session = Depends(get_db)):
    """Create a new focus area."""
    return create_focus_area(db, **area_data)


@router.get("/focus-areas", response_model=list[FocusAreaSchema])
def list_all_focus_areas(category: str = None, db: Session = Depends(get_db)):
    """List all focus areas."""
    return list_focus_areas(db, category=category)


@router.post("/routines", response_model=PersonalRoutineSchema)
def add_routine(routine_data: dict, db: Session = Depends(get_db)):
    """Create a personal routine."""
    return create_personal_routine(db, **routine_data)


@router.get("/routines", response_model=list[PersonalRoutineSchema])
def list_all_active_routines(db: Session = Depends(get_db)):
    """List all active routines."""
    return list_active_routines(db)


@router.post("/routines/{routine_id}/completion", response_model=RoutineCompletionSchema)
def log_completion(routine_id: int, completion_data: dict, db: Session = Depends(get_db)):
    """Log routine completion."""
    completion_data["routine_id"] = routine_id
    return log_routine_completion(db, **completion_data)


@router.get("/routines/{routine_id}/completion-rate", response_model=dict)
def get_completion_rate(routine_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get routine completion rate."""
    rate = get_routine_completion_rate(db, routine_id, days=days)
    return {"routine_id": routine_id, "completion_rate_percent": rate, "days": days}


@router.post("/family-snapshots", response_model=FamilySnapshotSchema)
def add_family_snapshot(snapshot_data: dict, db: Session = Depends(get_db)):
    """Create a family snapshot."""
    return create_family_snapshot(db, **snapshot_data)


@router.post("/dashboard/weekly", response_model=LifeDashboardSchema)
def create_weekly_dashboard(dashboard_data: dict, db: Session = Depends(get_db)):
    """Create a weekly life dashboard."""
    return create_life_dashboard(db, **dashboard_data)


@router.post("/goals", response_model=PersonalGoalSchema)
def add_goal(goal_data: dict, db: Session = Depends(get_db)):
    """Create a personal goal."""
    return create_personal_goal(db, **goal_data)


@router.get("/goals", response_model=list[PersonalGoalSchema])
def list_all_active_goals(db: Session = Depends(get_db)):
    """List all active goals."""
    return list_active_goals(db)


@router.put("/goals/{goal_id}/progress", response_model=PersonalGoalSchema)
def update_progress(goal_id: int, progress_percent: int, db: Session = Depends(get_db)):
    """Update goal progress."""
    goal = update_goal_progress(db, goal_id, progress_percent)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.post("/mood", response_model=MoodLogSchema)
def log_mood_entry(mood_data: dict, db: Session = Depends(get_db)):
    """Log a mood entry."""
    return log_mood(db, **mood_data)


@router.get("/mood/recent", response_model=list[MoodLogSchema])
def get_recent_mood(days: int = 30, db: Session = Depends(get_db)):
    """Get recent mood logs."""
    return get_mood_logs(db, days=days)


@router.get("/metrics", response_model=LifeOperationsResponse)
def get_life_metrics(db: Session = Depends(get_db)):
    """Get life operations metrics."""
    metrics = calculate_life_metrics(db)
    return LifeOperationsResponse(
        week_of=None,
        total_focus_areas=metrics["focus_areas"],
        active_routines=metrics["active_routines"],
        week_completion_rate=0.0,
        goals_on_track=metrics["active_goals"],
        total_goals=metrics["active_goals"] + metrics["completed_goals"],
        average_energy_level=metrics["average_energy_level"]
    )
