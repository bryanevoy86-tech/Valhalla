"""
PACK TQ: Security Policy Services
Business logic for policy and blocklist management.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.security_policy import SecurityPolicy, BlockedEntity


async def ensure_policy_row(db: Session) -> SecurityPolicy:
    """Ensure default policy exists, create if needed."""
    policy = db.query(SecurityPolicy).first()
    if not policy:
        policy = SecurityPolicy(
            default_mode="normal",
            auto_elevate=False,
            auto_lockdown=False,
            max_failed_auth=5,
            max_scan_events=10,
            notes="Default policy"
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy


async def get_policy(db: Session) -> SecurityPolicy:
    """Get current security policy."""
    return await ensure_policy_row(db)


async def update_policy(db: Session, **kwargs) -> SecurityPolicy:
    """Update security policy settings."""
    policy = await ensure_policy_row(db)
    for key, value in kwargs.items():
        if value is not None and hasattr(policy, key):
            setattr(policy, key, value)
    policy.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(policy)
    return policy


async def create_block(
    db: Session,
    entity_type: str,
    value: str,
    reason: str,
    expires_at: datetime = None
) -> BlockedEntity:
    """Create a blocked entity."""
    block = BlockedEntity(
        entity_type=entity_type,
        value=value,
        reason=reason,
        active=True,
        expires_at=expires_at
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


async def list_blocks(db: Session, active_only: bool = True):
    """List blocked entities."""
    query = db.query(BlockedEntity)
    
    if active_only:
        query = query.filter(BlockedEntity.active == True)
        now = datetime.utcnow()
        query = query.filter(
            (BlockedEntity.expires_at == None) |
            (BlockedEntity.expires_at > now)
        )
    
    items = query.order_by(desc(BlockedEntity.created_at)).all()
    total = db.query(BlockedEntity).count()
    active = db.query(BlockedEntity).filter(BlockedEntity.active == True).count()
    
    return {
        "total": total,
        "active": active,
        "items": items
    }


async def deactivate_block(db: Session, block_id: int) -> BlockedEntity:
    """Deactivate a blocked entity."""
    block = db.query(BlockedEntity).filter(BlockedEntity.id == block_id).first()
    if not block:
        return None
    
    block.active = False
    db.commit()
    db.refresh(block)
    return block


async def cleanup_expired_blocks(db: Session):
    """Deactivate expired blocks (optional cleanup task)."""
    now = datetime.utcnow()
    expired = db.query(BlockedEntity).filter(
        BlockedEntity.active == True,
        BlockedEntity.expires_at <= now
    ).all()
    
    for block in expired:
        block.active = False
    
    db.commit()
    return len(expired)
