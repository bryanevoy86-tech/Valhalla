from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.va_task_routing_engine import route_va_tasks

router = APIRouter(prefix="/heimdall/va-tasks", tags=["Heimdall VA Tasks"])


class VATaskRoutingRequest(BaseModel):
    command_result: Dict[str, Any]
    deal: Dict[str, Any]


@router.post("/route")
def route_tasks(payload: VATaskRoutingRequest):
    """
    Convert Heimdall command into exact VA tasks with priorities and deadlines.
    
    Routes differ by command:
    - HOLD_MISSING_INFORMATION / POSSIBLE_DEAL_MORE_DUE_DILIGENCE: Research tasks
    - BUILD_BUYER_LIST_FIRST: Buyer sourcing tasks
    - SOURCE_OR_MATCH_BUYERS_FIRST: Buyer matching tasks
    - RENEGOTIATE: Seller renegotiation prep tasks
    - STRONG_CANDIDATE_APPROVAL_REQUIRED: Full preparation + approval gates
    - PASS_OR_HOLD / PASS_OR_NURTURE: Nurture sequence tasks
    
    Returns:
    - tasks: List of task objects with title, priority, owner_role, due_at, approval_required
    - human_approval_required_for_critical_tasks: Always true for critical-priority tasks
    """
    return route_va_tasks(payload.command_result, payload.deal)
