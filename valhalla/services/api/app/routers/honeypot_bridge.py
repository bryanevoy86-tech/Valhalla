"""
PACK TS: Honeypot Bridge Routers
API endpoints for honeypot instance management and event reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.honeypot_bridge import (
    HoneypotInstanceCreate, HoneypotInstanceOut,
    HoneypotEventCreate, HoneypotEventOut, HoneypotEventList
)
from app.services import honeypot_bridge

router = APIRouter(prefix="/security/honeypot", tags=["Honeypot Bridge"])


@router.post("/instances", response_model=HoneypotInstanceOut)
async def create_instance(
    instance: HoneypotInstanceCreate,
    db: Session = Depends(get_db)
):
    """Create a new honeypot instance."""
    result = await honeypot_bridge.create_instance(
        db,
        name=instance.name,
        honeypot_type=instance.honeypot_type,
        location=instance.location,
        metadata=instance.metadata
    )
    return result


@router.get("/instances", response_model=list)
async def list_instances(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List honeypot instances."""
    result = await honeypot_bridge.list_instances(db, active_only=active_only)
    return result.get("items", [])


@router.post("/events", response_model=HoneypotEventOut)
async def record_event(
    event: HoneypotEventCreate,
    x_honeypot_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """Record a honeypot event (authenticated via X-HONEYPOT-KEY header)."""
    if not x_honeypot_key:
        raise HTTPException(status_code=401, detail="Missing X-HONEYPOT-KEY header")
    
    instance = await honeypot_bridge.get_instance_by_api_key(db, x_honeypot_key)
    if not instance:
        raise HTTPException(status_code=401, detail="Invalid honeypot API key")
    
    result = await honeypot_bridge.record_event(
        db,
        honeypot_id=instance.id,
        source_ip=event.source_ip,
        event_type=event.event_type,
        payload=event.payload,
        detected_threat=event.detected_threat
    )
    return result


@router.get("/events", response_model=HoneypotEventList)
async def list_events(
    honeypot_id: int = None,
    unprocessed_only: bool = False,
    db: Session = Depends(get_db)
):
    """List honeypot events."""
    result = await honeypot_bridge.list_events(
        db,
        honeypot_id=honeypot_id,
        unprocessed_only=unprocessed_only
    )
    return HoneypotEventList(
        total=result["total"],
        unprocessed=result["unprocessed"],
        items=result["items"]
    )


@router.post("/instances/{instance_id}/deactivate", response_model=HoneypotInstanceOut)
async def deactivate_instance(
    instance_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a honeypot instance."""
    result = await honeypot_bridge.deactivate_instance(db, instance_id)
    if not result:
        raise HTTPException(status_code=404, detail="Instance not found")
    return result
