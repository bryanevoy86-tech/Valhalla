from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.heimdall.education.persistence_models import (
    create_deal_record,
    get_deal_record,
    update_deal_record,
    list_deal_records,
    create_buyer_record,
    list_buyer_records,
    create_task_record,
    list_task_records,
    create_approval_record,
    update_approval_record,
    list_approval_records,
    create_message_record,
    list_message_records,
)

router = APIRouter(prefix="/heimdall/store", tags=["Heimdall Persistence"])


class GenericRecordRequest(BaseModel):
    data: Dict[str, Any]


class DealUpdateRequest(BaseModel):
    updates: Dict[str, Any]


class ApprovalUpdateRequest(BaseModel):
    status: str
    reviewed_by: str
    notes: str = ""


@router.post("/deals")
def create_deal(payload: GenericRecordRequest):
    """
    Create and store a new deal record.
    
    Returns: Deal object with auto-generated id, created_at, updated_at, state=NEW_LEAD
    """
    return create_deal_record(payload.data)


@router.get("/deals")
def list_deals():
    """
    Retrieve all deal records from persistence.
    
    Returns: List of all deals
    """
    return list_deal_records()


@router.get("/deals/{deal_id}")
def get_deal(deal_id: str):
    """
    Retrieve a specific deal record by ID.
    
    Returns: Deal object or 404 if not found
    """
    deal = get_deal_record(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.patch("/deals/{deal_id}")
def update_deal(deal_id: str, payload: DealUpdateRequest):
    """
    Update a deal record with new values.
    
    Updates: updated_at timestamp automatically set
    Returns: Updated deal object or 404 if not found
    """
    deal = update_deal_record(deal_id, payload.updates)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("/buyers")
def create_buyer(payload: GenericRecordRequest):
    """
    Create and store a new buyer record.
    
    Returns: Buyer object with auto-generated id, created_at, updated_at
    """
    return create_buyer_record(payload.data)


@router.get("/buyers")
def list_buyers():
    """
    Retrieve all buyer records from persistence.
    
    Returns: List of all buyers
    """
    return list_buyer_records()


@router.post("/tasks")
def create_task(payload: GenericRecordRequest):
    """
    Create and store a new VA task record.
    
    Returns: Task object with auto-generated id, created_at, updated_at
    """
    return create_task_record(payload.data)


@router.get("/tasks")
def list_tasks(deal_id: Optional[str] = None):
    """
    Retrieve VA task records, optionally filtered by deal_id.
    
    Query params:
    - deal_id: Optional filter to return only tasks for specific deal
    
    Returns: List of task objects
    """
    return list_task_records(deal_id)


@router.post("/approvals")
def create_approval(payload: GenericRecordRequest):
    """
    Create and store a new approval record.
    
    Returns: Approval object with auto-generated id, status=PENDING, created_at, updated_at
    """
    return create_approval_record(payload.data)


@router.get("/approvals")
def list_approvals():
    """
    Retrieve all approval records from persistence.
    
    Returns: List of all approvals with their current status (PENDING, APPROVED, REJECTED)
    """
    return list_approval_records()


@router.patch("/approvals/{approval_id}")
def update_approval(approval_id: str, payload: ApprovalUpdateRequest):
    """
    Update an approval record with decision.
    
    Updates: status, reviewed_by, reviewed_at, review_notes, updated_at
    Returns: Updated approval object or 404 if not found
    """
    approval = update_approval_record(
        approval_id=approval_id,
        status=payload.status,
        reviewed_by=payload.reviewed_by,
        notes=payload.notes,
    )
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/messages")
def create_message(payload: GenericRecordRequest):
    """
    Create and store a new message record (seller/buyer outreach).
    
    Returns: Message object with auto-generated id, status=DRAFT, created_at, updated_at
    """
    return create_message_record(payload.data)


@router.get("/messages")
def list_messages(deal_id: Optional[str] = None):
    """
    Retrieve message records, optionally filtered by deal_id.
    
    Query params:
    - deal_id: Optional filter to return only messages for specific deal
    
    Returns: List of message objects with their current status (DRAFT, APPROVED, SENT)
    """
    return list_message_records(deal_id)
