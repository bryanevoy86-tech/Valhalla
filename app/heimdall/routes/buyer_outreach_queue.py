from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from app.heimdall.education.buyer_outreach_queue import (
    build_buyer_outreach_queue,
    approve_buyer_outreach,
    reject_buyer_outreach,
)

router = APIRouter(prefix="/heimdall/buyer-outreach", tags=["Heimdall Buyer Outreach"])


class BuyerOutreachQueueRequest(BaseModel):
    deal: Dict[str, Any]
    matched_buyers: List[Dict[str, Any]]


class BuyerOutreachApproveRequest(BaseModel):
    queue_item: Dict[str, Any]
    approved_by: str


class BuyerOutreachRejectRequest(BaseModel):
    queue_item: Dict[str, Any]
    rejected_by: str
    reason: str


@router.post("/queue")
def create_buyer_outreach_queue(payload: BuyerOutreachQueueRequest):
    """
    Build buyer outreach approval queue for a deal.
    
    Takes matched buyers (score >= 60) and drafts pre-approval messages.
    All messages held in PENDING_APPROVAL status until human review.
    
    Returns:
    - approval_queue: List of queue items with drafted messages
    - queue_count: Number of qualified buyers in queue
    - send_blocked_until_approved: Always true (no auto-sending)
    """
    return build_buyer_outreach_queue(payload.deal, payload.matched_buyers)


@router.post("/approve")
def approve_outreach(payload: BuyerOutreachApproveRequest):
    """
    Approve a buyer outreach message for sending.
    
    Returns:
    - status: Changed to APPROVED_TO_SEND
    - approved_by: User who approved
    - approved_at: Timestamp
    - send_allowed: Now true
    """
    return approve_buyer_outreach(payload.queue_item, payload.approved_by)


@router.post("/reject")
def reject_outreach(payload: BuyerOutreachRejectRequest):
    """
    Reject a buyer outreach message.
    
    Returns:
    - status: Changed to REJECTED
    - rejected_by: User who rejected
    - rejection_reason: Reason for rejection
    - send_allowed: False
    """
    return reject_buyer_outreach(payload.queue_item, payload.rejected_by, payload.reason)
