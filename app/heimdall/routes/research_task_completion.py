"""
Research Task Completion Route
Prefix: /heimdall/research-tasks
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.research_task_completion_service import (
    complete_research_task,
)

router = APIRouter(
    prefix="/heimdall/research-tasks",
    tags=["Heimdall Research Tasks"],
)


class ResearchTaskCompletionRequest(BaseModel):
    completed_by: str
    findings: Dict[str, Any]
    notes: str = ""


@router.post("/{task_id}/complete")
def complete_task(
    task_id: str,
    payload: ResearchTaskCompletionRequest,
    db: Session = Depends(get_db),
):
    """
    Complete a research task and update property intel record with findings.

    **Process:**
    1. Mark task COMPLETED
    2. Merge findings into property data
    3. Recalculate property distress score + lead lane
    4. Return updated property status

    **Example Request:**
    ```json
    {
        "completed_by": "VA_Research",
        "findings": {
            "ownership_unverified": false,
            "owner_name": "John Smith",
            "tax_arrears_known": true,
            "out_of_area_owner": true,
            "estimated_arv": 240000
        },
        "notes": "Assessment checked, owner and tax arrears signal added."
    }
    ```

    **Response:**
    ```json
    {
        "status": "RESEARCH_TASK_COMPLETED",
        "task_id": "task_123",
        "property_intel_id": "propintel_abc",
        "property_research_status": "RESEARCH_COMPLETE",
        "property_distress_score": 82,
        "property_lead_lane": "HIGH_PRIORITY_RESEARCH_AND_OUTREACH",
        "outreach_allowed": true,
        "ownership_verified": true
    }
    ```

    Findings dict is merged into property_data, which recalculates distress scoring.
    """
    return complete_research_task(
        db=db,
        task_id=task_id,
        completed_by=payload.completed_by,
        findings=payload.findings,
        notes=payload.notes,
    )
