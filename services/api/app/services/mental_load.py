"""
PACK SN: Mental Load Offloading Engine
Service functions for brain externalization and task management
"""
from sqlalchemy.orm import Session
from app.models.mental_load import MentalLoadEntry, DailyLoadSummary, LoadOffloadWorkflow
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


def add_mental_load_entry(
    db: Session,
    entry_id: str,
    category: str,
    description: str,
    urgency_level: Optional[int] = None,
    emotional_weight: Optional[int] = None,
    action_required: bool = False,
    user_notes: Optional[str] = None
) -> MentalLoadEntry:
    """Add an item to mental load."""
    entry = MentalLoadEntry(
        entry_id=entry_id,
        category=category,
        description=description,
        urgency_level=urgency_level,
        emotional_weight=emotional_weight,
        action_required=action_required,
        user_notes=user_notes
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_pending_load(db: Session) -> List[MentalLoadEntry]:
    """Get all pending (uncleared) mental load entries."""
    return db.query(MentalLoadEntry).filter(
        MentalLoadEntry.cleared == False
    ).order_by(MentalLoadEntry.urgency_level.desc()).all()


def get_load_by_category(db: Session, category: str) -> List[MentalLoadEntry]:
    """Get mental load entries by category."""
    return db.query(MentalLoadEntry).filter(
        MentalLoadEntry.category == category,
        MentalLoadEntry.cleared == False
    ).all()


def clear_load_entry(db: Session, entry_id: int) -> MentalLoadEntry:
    """Mark a mental load entry as cleared."""
    entry = db.query(MentalLoadEntry).filter(MentalLoadEntry.id == entry_id).first()
    if entry:
        entry.cleared = True
        entry.cleared_date = datetime.utcnow()
        db.commit()
        db.refresh(entry)
    return entry


def create_daily_summary(
    db: Session,
    summary_id: str,
    date: datetime,
    total_items: int,
    urgent_items: Optional[List[str]] = None,
    action_items: Optional[List[str]] = None,
    delegated_items: Optional[List[str]] = None,
    cleared_items: Optional[List[str]] = None,
    waiting_items: Optional[List[str]] = None,
    parked_items: Optional[List[str]] = None,
    notes: Optional[str] = None
) -> DailyLoadSummary:
    """Create a daily load summary."""
    summary = DailyLoadSummary(
        summary_id=summary_id,
        date=date,
        total_items=total_items,
        urgent_items=urgent_items,
        action_items=action_items,
        delegated_items=delegated_items,
        cleared_items=cleared_items,
        waiting_items=waiting_items,
        parked_items=parked_items,
        notes=notes
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def start_brain_dump_workflow(
    db: Session,
    workflow_id: str,
    brain_dump: str
) -> LoadOffloadWorkflow:
    """Start a rapid brain dump workflow."""
    workflow = LoadOffloadWorkflow(
        workflow_id=workflow_id,
        brain_dump=brain_dump,
        workflow_stage="intake"
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def categorize_brain_dump(
    db: Session,
    workflow_id: int,
    categorized_items: List[Dict[str, Any]]
) -> LoadOffloadWorkflow:
    """Update workflow with categorized items."""
    workflow = db.query(LoadOffloadWorkflow).filter(LoadOffloadWorkflow.id == workflow_id).first()
    if workflow:
        workflow.categorized_items = categorized_items
        workflow.processed_count = len(categorized_items)
        workflow.workflow_stage = "categorizing"
        db.commit()
        db.refresh(workflow)
    return workflow


def calculate_cognitive_load(db: Session) -> Dict[str, Any]:
    """Calculate current cognitive load metrics."""
    all_entries = db.query(MentalLoadEntry).filter(MentalLoadEntry.cleared == False).all()
    
    urgent = [e for e in all_entries if e.urgency_level and e.urgency_level >= 4]
    action = [e for e in all_entries if e.action_required]
    
    total_weight = sum(e.emotional_weight or 0 for e in all_entries)
    cognitive_pressure = min(100, (total_weight / max(1, len(all_entries))) * 10) if all_entries else 0
    
    categories = {}
    for entry in all_entries:
        categories[entry.category] = categories.get(entry.category, 0) + 1
    
    return {
        "total_items": len(all_entries),
        "urgent_count": len(urgent),
        "action_count": len(action),
        "cognitive_pressure": cognitive_pressure,
        "by_category": categories,
        "focus_areas": [e.description for e in urgent[:5]]
    }


def clear_daily_board(db: Session, before_date: datetime) -> int:
    """Clear items that were resolved before a date."""
    cleared_count = db.query(MentalLoadEntry).filter(
        MentalLoadEntry.cleared_date < before_date
    ).count()
    
    db.query(MentalLoadEntry).filter(
        MentalLoadEntry.cleared_date < before_date
    ).delete()
    db.commit()
    
    return cleared_count
