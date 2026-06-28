from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.owner_outreach_approval_service import (
    create_owner_outreach_approval,
)

router = APIRouter(
    prefix="/heimdall/owner-outreach-approval",
    tags=["Heimdall Owner Outreach Approval"],
)


class OwnerOutreachApprovalRequest(BaseModel):
    property_record: Dict[str, Any]
    created_by: str = "heimdall"


@router.post("/create")
def create_approval(payload: OwnerOutreachApprovalRequest, db: Session = Depends(get_db)):
    """
    Create owner outreach approval item.
    
    Creates paired records:
    1. Approval record (PENDING) — for human approval
    2. Message record (DRAFT_PENDING_APPROVAL) — for send gating
    
    Input: property_record with distress_analysis and property_data
    Output: approval_id, message_id, draft_letter packet
    
    Message sending is blocked until approval is APPROVED
    (via POST /heimdall/approvals/{approval_id}/execute)
    """
    return create_owner_outreach_approval(
        db=db,
        property_record=payload.property_record,
        created_by=payload.created_by,
    )
