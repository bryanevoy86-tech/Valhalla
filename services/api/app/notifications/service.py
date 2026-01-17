from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .schemas import Notification, NotificationOut


# In-memory storage for demo (replace with DB persistence in production)
_NOTIFICATIONS: List[Notification] = []


class NotificationService:
    """Service for managing real-time notifications."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def create_notification(user_id: str, content: str) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            content=content,
            timestamp=datetime.utcnow(),
            is_read=False
        )
        _NOTIFICATIONS.append(notification)
        return notification
    
    @staticmethod
    def get_notifications(user_id: Optional[str] = None, limit: int = 50) -> List[Notification]:
        """
        Get notifications, optionally filtered by user_id.
        Returns most recent notifications first.
        """
        notifications = _NOTIFICATIONS
        
        if user_id:
            notifications = [n for n in notifications if n.user_id == user_id]
        
        # Return most recent first
        notifications = sorted(notifications, key=lambda n: n.timestamp, reverse=True)
        
        return notifications[:limit]
    
    @staticmethod
    def mark_as_read(user_id: str, index: int) -> bool:
        """
        Mark a notification as read.
        Returns True if successful, False if not found.
        """
        user_notifications = [n for n in _NOTIFICATIONS if n.user_id == user_id]
        
        if 0 <= index < len(user_notifications):
            # Find the notification in the global list and mark it as read
            notification = user_notifications[index]
            notification.is_read = True
            return True
        
        return False
    
    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get count of unread notifications for a user."""
        return sum(1 for n in _NOTIFICATIONS if n.user_id == user_id and not n.is_read)
