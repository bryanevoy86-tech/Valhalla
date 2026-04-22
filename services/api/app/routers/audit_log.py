"""
Audit log router - retrieve audit trail events.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..core.db import get_db
from ..models.audit_log import AuditLog
from ..schemas.audit_log import AuditLogOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("", response_model=List[AuditLogOut])
def get_audit_log(
    deal_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get audit log entries, optionally filtered by deal_id.
    
    Returns latest events first.
    
    Args:
        deal_id: Optional deal ID to filter by
        limit: Maximum number of entries to return (default 50)
        db: Database session
    
    Returns:
        List of AuditLogOut sorted by created_at DESC
    """
    try:
        query = db.query(AuditLog)
        
        if deal_id is not None:
            query = query.filter(AuditLog.deal_id == deal_id)
        
        entries = query.order_by(
            desc(AuditLog.created_at)
        ).limit(limit).all()
        
        logger.info(f"Retrieved {len(entries)} audit log entries (deal_id={deal_id})")
        return entries
        
    except Exception as err:
        logger.error(f"Failed to retrieve audit log: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve audit log", "message": str(err)}
        )
