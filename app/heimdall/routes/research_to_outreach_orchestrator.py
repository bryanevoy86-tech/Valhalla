from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.research_to_outreach_orchestrator import (
    run_research_to_outreach_orchestrator,
)

router = APIRouter(
    prefix="/heimdall/research-outreach",
    tags=["Heimdall Research → Outreach"],
)


class ResearchToOutreachRequest(BaseModel):
    property_intel_id: str
    created_by: str = "heimdall"


@router.post("/orchestrate")
def orchestrate_research_to_outreach(
    payload: ResearchToOutreachRequest,
    db: Session = Depends(get_db),
):
    """
    Chain: Research Readiness Check → Auto-Generate Owner Outreach Letter & Approval.
    
    If research is incomplete (blockers present):
      - Return NOT_READY_FOR_OUTREACH with list of blockers
      - VA resolves blockers and tries again
    
    If research is complete (all 5-point check passes):
      - Automatically generate owner outreach letter
      - Create approval record (PENDING human review)
      - Create message draft (blocked until approval)
      - Return complete outreach packet ready for human approval
    
    Request:
      {
        "property_intel_id": "propintel_abc123",
        "created_by": "VA_Seller_Support"
      }
    
    Response (Ready):
      {
        "status": "READY_FOR_OUTREACH_APPROVAL",
        "readiness_evaluation": {...},
        "outreach_packet": {
          "approval_result": {...},
          "approval_id": "approval_xyz123",
          "message_id": "msg_xyz123"
        },
        "next_steps": ["Review letter", "Approve outreach", "Send to recipient"]
      }
    
    Response (Not Ready):
      {
        "status": "RESEARCH_INCOMPLETE",
        "blockers": ["missing_required_research", "research_tasks_still_open"],
        "missing_required": ["owner_name"],
        "next_action": "Complete required research and resolve blockers before outreach."
      }
    """
    return run_research_to_outreach_orchestrator(
        db=db,
        property_intel_id=payload.property_intel_id,
        created_by=payload.created_by,
    )
