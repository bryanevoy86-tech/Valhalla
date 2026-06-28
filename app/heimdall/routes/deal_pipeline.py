from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.deal_pipeline_state_machine import (
    advance_deal_state,
    get_pipeline_requirements,
)

router = APIRouter(prefix="/heimdall/pipeline", tags=["Heimdall Deal Pipeline"])


class DealStateAdvanceRequest(BaseModel):
    deal: Dict[str, Any]
    command_result: Dict[str, Any]
    advanced_by: str = "heimdall"


@router.post("/advance")
def advance_state(payload: DealStateAdvanceRequest):
    """
    Advance deal through pipeline based on Heimdall command.
    
    Validates state transition against ALLOWED_TRANSITIONS mapping.
    Maps command to recommended next state via COMMAND_TO_STATE.
    
    Returns:
    - updated_deal: Deal object with new state and state_history entry
    - state_changed: Whether state actually transitioned
    - previous_state/new_state: For tracking
    - human_review_required: True if new state is LAWYER_REVIEW, APPROVAL_REQUIRED, or CONTRACT_PENDING
    - error: If transition not allowed (includes allowed next states)
    """
    return advance_deal_state(
        deal=payload.deal,
        command_result=payload.command_result,
        advanced_by=payload.advanced_by,
    )


@router.get("/requirements/{state}")
def pipeline_requirements(state: str):
    """
    Get pipeline requirements checklist for a given state.
    
    Returns list of items needed before deal can advance from this state.
    
    Example: GET /heimdall/pipeline/requirements/LAWYER_REVIEW returns:
    ["Lawyer packet", "Draft terms", "Authority docs"]
    """
    return get_pipeline_requirements(state)
