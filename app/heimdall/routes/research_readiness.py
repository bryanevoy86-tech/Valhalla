"""
Research Completion Readiness Route
Prefix: /heimdall/research-readiness
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.research_readiness_service import (
    evaluate_research_readiness,
)

router = APIRouter(
    prefix="/heimdall/research-readiness",
    tags=["Heimdall Research Readiness"],
)


class ResearchReadinessRequest(BaseModel):
    property_intel_id: str


@router.post("/evaluate")
def evaluate_readiness(
    payload: ResearchReadinessRequest,
    db: Session = Depends(get_db),
):
    """
    Evaluate whether a property has enough research to proceed with owner outreach.

    **Checks:**
    1. ✓ Required findings: owner_name, ownership_unverified, estimated_arv
    2. ✓ Ownership verified (not unverified)
    3. ✓ Distress score ≥50
    4. ✓ Property status allows outreach (not DO_NOT_CONTACT or OUTREACH_BLOCKED)
    5. ✓ All research tasks completed (no OPEN/PENDING tasks)

    **If ALL checks pass:**
    - Property marked READY_FOR_OUTREACH
    - Outreach allowed flag enabled
    - Return next_action: Generate outreach packet

    **If ANY check fails:**
    - Return blocker codes + specific missing fields
    - Return next_action: Complete missing research

    **Request:**
    ```json
    {
        "property_intel_id": "propintel_abc123"
    }
    ```

    **Response (Ready):**
    ```json
    {
        "status": "READY_FOR_OUTREACH",
        "property_intel_id": "propintel_abc123",
        "missing_recommended": ["tax_arrears_known", "recent_sales_checked"],
        "distress_score": 78,
        "research_status": "READY_FOR_OUTREACH",
        "outreach_allowed": true,
        "next_action": "Generate owner outreach approval packet."
    }
    ```

    **Response (Not Ready):**
    ```json
    {
        "status": "NOT_READY_FOR_OUTREACH",
        "property_intel_id": "propintel_abc123",
        "blockers": ["missing_required_research", "ownership_not_verified"],
        "missing_required": ["owner_name"],
        "missing_recommended": ["tax_arrears_known"],
        "open_task_count": 2,
        "distress_score": 45,
        "research_status": "RESEARCH_REQUIRED",
        "next_action": "Complete required research and resolve blockers."
    }
    ```
    """
    return evaluate_research_readiness(
        db=db,
        property_intel_id=payload.property_intel_id,
    )
