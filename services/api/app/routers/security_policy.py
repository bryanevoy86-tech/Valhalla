"""
PACK TQ: Security Policy Routers
API endpoints for policy and blocklist management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.security_policy import BlockedEntity
from app.schemas.security_policy import (
    SecurityPolicyOut, SecurityPolicyUpdate,
    BlockedEntityCreate, BlockedEntityOut, BlockedEntityList
)
from app.services import security_policy

router = APIRouter(prefix="/security/policy", tags=["Security Policy"])


@router.get("/", response_model=SecurityPolicyOut)
async def get_policy(db: Session = Depends(get_db)):
    """Get current security policy."""
    policy = await security_policy.get_policy(db)
    return policy


@router.post("/", response_model=SecurityPolicyOut)
async def update_policy(
    update: SecurityPolicyUpdate,
    db: Session = Depends(get_db)
):
    """Update security policy settings."""
    policy = await security_policy.update_policy(
        db,
        default_mode=update.default_mode,
        auto_elevate=update.auto_elevate,
        auto_lockdown=update.auto_lockdown,
        max_failed_auth=update.max_failed_auth,
        max_scan_events=update.max_scan_events,
        notes=update.notes
    )
    return policy


@router.post("/blocks", response_model=BlockedEntityOut)
async def create_block(
    block: BlockedEntityCreate,
    db: Session = Depends(get_db)
):
    """Create a blocked entity (IP, user, or API key)."""
    result = await security_policy.create_block(
        db,
        entity_type=block.entity_type,
        value=block.value,
        reason=block.reason,
        expires_at=block.expires_at
    )
    return result


@router.get("/blocks", response_model=BlockedEntityList)
async def list_blocks(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List blocked entities."""
    result = await security_policy.list_blocks(db, active_only=active_only)
    return BlockedEntityList(
        total=result["total"],
        active=result["active"],
        items=result["items"]
    )


@router.post("/blocks/{block_id}/deactivate", response_model=BlockedEntityOut)
async def deactivate_block(
    block_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a blocked entity."""
    block = await security_policy.deactivate_block(db, block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return block
