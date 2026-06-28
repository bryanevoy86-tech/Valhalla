from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.heimdall.services.persistence_service import (
    create_deal,
    list_deals,
    get_deal,
    update_deal,
    create_buyer,
    list_buyers,
    create_task,
    list_tasks,
    create_approval,
    list_approvals,
    update_approval,
    create_message,
    list_messages,
)

router = APIRouter(prefix="/heimdall/db", tags=["Heimdall Database Persistence"])


class GenericRecordRequest(BaseModel):
    data: Dict[str, Any]


class DealUpdateRequest(BaseModel):
    updates: Dict[str, Any]


class ApprovalUpdateRequest(BaseModel):
    status: str
    reviewed_by: str
    notes: str = ""


def serialize(record):
    return {
        "id": record.id,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        **(record.data or {}),
    }


@router.post("/deals")
def create_deal_route(payload: GenericRecordRequest, db: Session = Depends(get_db)):
    """
    Create and store a new deal record in database.
    
    Returns: Deal object with auto-generated id, created_at, updated_at, state=NEW_LEAD
    """
    return serialize(create_deal(db, payload.data))


@router.get("/deals")
def list_deals_route(db: Session = Depends(get_db)):
    """
    Retrieve all deal records from database.
    
    Returns: List of all deals (most recent first)
    """
    return [serialize(record) for record in list_deals(db)]


@router.get("/deals/{deal_id}")
def get_deal_route(deal_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a specific deal record by ID.
    
    Returns: Deal object or 404 if not found
    """
    record = get_deal(db, deal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return serialize(record)


@router.patch("/deals/{deal_id}")
def update_deal_route(deal_id: str, payload: DealUpdateRequest, db: Session = Depends(get_db)):
    """
    Update a deal record with new values.
    
    Merges updates into existing data, updates state if provided.
    Updates: updated_at timestamp automatically set
    Returns: Updated deal object or 404 if not found
    """
    record = update_deal(db, deal_id, payload.updates)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return serialize(record)


@router.post("/buyers")
def create_buyer_route(payload: GenericRecordRequest, db: Session = Depends(get_db)):
    """
    Create and store a new buyer record in database.
    
    Returns: Buyer object with auto-generated id, created_at, updated_at
    """
    return serialize(create_buyer(db, payload.data))


@router.get("/buyers")
def list_buyers_route(db: Session = Depends(get_db)):
    """
    Retrieve all buyer records from database.
    
    Returns: List of all buyers (most recent first)
    """
    return [serialize(record) for record in list_buyers(db)]


@router.post("/tasks")
def create_task_route(payload: GenericRecordRequest, db: Session = Depends(get_db)):
    """
    Create and store a new VA task record in database.
    
    Returns: Task object with auto-generated id, created_at, updated_at
    """
    return serialize(create_task(db, payload.data))


@router.get("/tasks")
def list_tasks_route(deal_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retrieve VA task records from database, optionally filtered by deal_id.
    
    Query params:
    - deal_id: Optional filter to return only tasks for specific deal
    
    Returns: List of task objects (most recent first)
    """
    return [serialize(record) for record in list_tasks(db, deal_id)]


@router.post("/approvals")
def create_approval_route(payload: GenericRecordRequest, db: Session = Depends(get_db)):
    """
    Create and store a new approval record in database.
    
    Returns: Approval object with auto-generated id, status=PENDING, created_at, updated_at
    """
    return serialize(create_approval(db, payload.data))


@router.get("/approvals")
def list_approvals_route(db: Session = Depends(get_db)):
    """
    Retrieve all approval records from database.
    
    Returns: List of all approvals with their current status (most recent first)
    """
    return [serialize(record) for record in list_approvals(db)]


@router.patch("/approvals/{approval_id}")
def update_approval_route(
    approval_id: str,
    payload: ApprovalUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update an approval record with decision.
    
    Updates: status, reviewed_by, reviewed_at, review_notes, updated_at
    Returns: Updated approval object or 404 if not found
    """
    record = update_approval(
        db=db,
        approval_id=approval_id,
        status=payload.status,
        reviewed_by=payload.reviewed_by,
        notes=payload.notes,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Approval not found")
    return serialize(record)


@router.post("/messages")
def create_message_route(payload: GenericRecordRequest, db: Session = Depends(get_db)):
    """
    Create and store a new message record (seller/buyer outreach) in database.
    
    Returns: Message object with auto-generated id, status=DRAFT, created_at, updated_at
    """
    return serialize(create_message(db, payload.data))


@router.get("/messages")
def list_messages_route(deal_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retrieve message records from database, optionally filtered by deal_id.
    
    Query params:
    - deal_id: Optional filter to return only messages for specific deal
    
    Returns: List of message objects (most recent first)
    """
    return [serialize(record) for record in list_messages(db, deal_id)]
