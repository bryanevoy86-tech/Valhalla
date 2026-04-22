"""
Deal notifications router - track and retrieve deal events.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..core.db import get_db
from ..models.deal_notification import DealNotification
from ..models.match import DealBrief
from ..schemas.deal_notifications import DealNotificationOut, DealNotificationIn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[DealNotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get latest notifications first.
    
    Args:
        db: Database session
        limit: Maximum number of notifications to return (default 50)
    
    Returns:
        List of DealNotificationOut sorted by created_at DESC
    """
    try:
        notifications = db.query(DealNotification).order_by(
            desc(DealNotification.created_at)
        ).limit(limit).all()
        
        logger.info(f"Retrieved {len(notifications)} notifications")
        return notifications
        
    except Exception as err:
        logger.error(f"Failed to list notifications: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to retrieve notifications", "message": str(err)}
        )


@router.post("/test", response_model=DealNotificationOut)
def create_test_notification(
    db: Session = Depends(get_db)
):
    """
    Create a sample test notification.
    
    Args:
        db: Database session
    
    Returns:
        Created test notification
    """
    try:
        notification = DealNotification(
            deal_id=None,
            type="test",
            title="Test Notification",
            message="This is a test notification to verify the notification system is working.",
            is_read=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        logger.info(f"Test notification created with id: {notification.id}")
        return notification
        
    except Exception as err:
        logger.error(f"Failed to create test notification: {str(err)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create test notification", "message": str(err)}
        )
