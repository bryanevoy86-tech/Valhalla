"""
Audit service for logging deal events.
"""

import logging
import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    deal_id: Optional[int] = None,
    event_type: str = "",
    message: str = "",
    metadata: Optional[dict] = None,
    event_source: str = "system"
) -> Optional[AuditLog]:
    """
    Log an audit event to the audit_log table.
    
    Args:
        db: Database session
        deal_id: Optional deal ID associated with the event
        event_type: Type of event (e.g., "deal_created", "deal_analyzed")
        message: Human-readable message about the event
        metadata: Optional dictionary of additional data (will be JSON serialized)
        event_source: Source of event - "system" or "user" (default "system")
    
    Returns:
        Created AuditLog object or None if error
    """
    try:
        # Serialize metadata to JSON string if provided
        event_data_str = None
        if metadata:
            try:
                event_data_str = json.dumps(metadata)
            except Exception as e:
                logger.warning(f"Failed to serialize metadata: {e}")
                event_data_str = str(metadata)
        
        # Create audit log entry
        audit_entry = AuditLog(
            deal_id=deal_id,
            event_type=event_type,
            event_source=event_source,
            message=message,
            event_data=event_data_str
        )
        
        db.add(audit_entry)
        db.commit()
        
        logger.debug(f"Audit event logged: {event_type} for deal_id={deal_id}")
        return audit_entry
        
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}", exc_info=True)
        db.rollback()
        return None
