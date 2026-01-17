"""
P-APPROVALGATE-1: Approval gate API router.

POST /core/approval_gate - Check approval requirement and gate
"""
from fastapi import APIRouter
from typing import Dict, Any
from pydantic import BaseModel
from . import service

router = APIRouter(prefix="/core", tags=["approval_gate"])


class ApprovalGateRequest(BaseModel):
    """Approval gate request model."""
    action: str
    payload: Dict[str, Any]


@router.post("/approval_gate", response_model=Dict[str, Any])
async def check_approval_gate(req: ApprovalGateRequest) -> Dict[str, Any]:
    """
    Check if an action requires approval.
    
    Args:
        req: Request with action and payload
    
    Returns:
        Approval gate response with requires_approval, approved, and approval_id
    """
    return service.require_execute_approval(req.action, req.payload)
