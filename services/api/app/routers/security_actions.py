"""
PACK TR: Security Action Routers
API endpoints for action request workflow and approvals.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.security_actions import (
    SecurityActionRequestCreate, SecurityActionRequestUpdate,
    SecurityActionRequestOut, SecurityActionRequestList
)
from app.services import security_actions

router = APIRouter(prefix="/security/actions", tags=["Security Actions"])


@router.post("/", response_model=SecurityActionRequestOut)
async def create_action_request(
    action: SecurityActionRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new security action request."""
    result = await security_actions.create_action_request(
        db,
        requested_by=action.requested_by,
        action_type=action.action_type,
        payload=action.payload
    )
    return result


@router.get("/", response_model=SecurityActionRequestList)
async def list_action_requests(
    status: str = None,
    db: Session = Depends(get_db)
):
    """List action requests, optionally filtered by status."""
    result = await security_actions.list_action_requests(db, status=status)
    return SecurityActionRequestList(
        total=result["total"],
        pending=result["pending"],
        items=result["items"]
    )


@router.get("/{request_id}", response_model=SecurityActionRequestOut)
async def get_action_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific action request."""
    result = await security_actions.get_action_request(db, request_id)
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return result


@router.post("/{request_id}", response_model=SecurityActionRequestOut)
async def update_action_request(
    request_id: int,
    update: SecurityActionRequestUpdate,
    db: Session = Depends(get_db)
):
    """Approve, reject, or execute an action request."""
    result = await security_actions.update_action_request(
        db,
        request_id,
        status=update.status,
        approved_by=update.approved_by,
        resolution_notes=update.resolution_notes,
        executed=(update.status == "executed")
    )
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")
    return result
