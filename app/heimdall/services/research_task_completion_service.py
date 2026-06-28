"""
Research Task Completion Service

VA completes research tasks and updates property intel record with findings.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallTask
from app.heimdall.services.property_intel_service import (
    get_property_intel_record,
    update_property_intel_research,
)


def complete_research_task(
    db: Session,
    task_id: str,
    completed_by: str,
    findings: Dict[str, Any],
    notes: str = "",
) -> Dict[str, Any]:
    """
    Complete a research task and update property intel record.

    Steps:
    1. Fetch task by ID
    2. Get associated property intel record
    3. Merge findings into property data
    4. Update property intel record with recalculated scores
    5. Mark task COMPLETED with audit trail
    6. Return updated property status

    Args:
        db: SQLAlchemy session
        task_id: Task ID to complete
        completed_by: VA/user identifier for audit trail
        findings: Dict of research findings to merge (e.g., {"ownership_unverified": false})
        notes: Optional notes about the research

    Returns:
        {
            "status": "RESEARCH_TASK_COMPLETED" | "ERROR",
            "task_id": str,
            "property_intel_id": str,
            "property_research_status": str,
            "property_distress_score": int,
            "property_lead_lane": str,
            "outreach_allowed": bool,
            "ownership_verified": bool,
        }
    """

    task = db.query(HeimdallTask).filter(HeimdallTask.id == task_id).first()

    if not task:
        return {
            "status": "ERROR",
            "reason": "Task not found.",
            "task_id": task_id,
        }

    property_intel_id = task.deal_id

    record = get_property_intel_record(db, property_intel_id)

    if not record:
        return {
            "status": "ERROR",
            "reason": "Property intel record not found for task.",
            "task_id": task_id,
            "property_intel_id": property_intel_id,
        }

    # Create completion note for audit trail
    completion_note = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "research_task_completed",
        "task_id": task_id,
        "task_title": task.title,
        "completed_by": completed_by,
        "findings": findings,
        "notes": notes,
    }

    # Merge findings into property data
    updated_property_data = {
        **(record.property_data or {}),
        **findings,
    }

    # Update property intel record (recalculates distress score, lane, etc.)
    updated_record = update_property_intel_research(
        db=db,
        record_id=property_intel_id,
        property_data=updated_property_data,
        notes=[completion_note],
    )

    # Update task status to COMPLETED
    task.status = "COMPLETED"
    task.data = {
        **(task.data or {}),
        "completed_by": completed_by,
        "completed_at": datetime.utcnow().isoformat(),
        "findings": findings,
        "notes": notes,
    }
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    return {
        "status": "RESEARCH_TASK_COMPLETED",
        "task_id": task.id,
        "property_intel_id": property_intel_id,
        "property_research_status": updated_record.research_status if updated_record else None,
        "property_distress_score": updated_record.distress_score if updated_record else None,
        "property_lead_lane": updated_record.lead_lane if updated_record else None,
        "outreach_allowed": updated_record.outreach_allowed if updated_record else None,
        "ownership_verified": updated_record.ownership_verified if updated_record else None,
    }
