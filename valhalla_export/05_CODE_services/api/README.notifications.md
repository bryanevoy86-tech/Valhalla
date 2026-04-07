# Pack 23: Real-Time Notifications

## Overview

This pack adds a comprehensive real-time notification system to your application. Users can receive immediate alerts for important events, view their notification history, and manage read/unread status. The system is designed for easy integration with WebSockets or push notification services in the future.

## Features

- **Create Notifications**: Send notifications to specific users with custom content
- **List Notifications**: Retrieve notifications with optional user filtering
- **Mark as Read**: Track which notifications users have seen
- **Unread Count**: Get a count of unread notifications per user
- **Interactive Dashboard**: Full-featured UI for testing and demonstration
- **Auto-Refresh**: Dashboard automatically updates every 5 seconds
- **In-Memory Storage**: Fast access with sliding window (last 1000 notifications retained)

## Endpoints

### POST `/api/notifications/create`

Create a new notification for a user.

**Request Body:**
```json
{
  "user_id": "user_123",
  "content": "Your order has been shipped!"
}
```

**Response:**
```json
{
  "user_id": "user_123",
  "content": "Your order has been shipped!",
  "timestamp": "2025-11-05T10:30:00.123456",
  "is_read": false
}
```

### GET `/api/notifications/list`

Get notifications, optionally filtered by user.

**Query Parameters:**
- `user_id` (string, optional): Filter notifications for a specific user
- `limit` (integer, optional, default=50): Maximum number of notifications to return

**Response:**
```json
[
  {
    "user_id": "user_123",
    "content": "Your order has been shipped!",
    "timestamp": "2025-11-05T10:30:00.123456",
    "is_read": false
  },
  {
    "user_id": "user_123",
    "content": "New message from support",
    "timestamp": "2025-11-05T09:15:00.789012",
    "is_read": true
  }
]
```

### POST `/api/notifications/mark-read/{user_id}/{index}`

Mark a specific notification as read for a user.

**Path Parameters:**
- `user_id` (string): The user's ID
- `index` (integer): The index of the notification in the user's list (0-based)

**Response:**
```json
{
  "ok": true,
  "message": "Notification marked as read"
}
```

### GET `/api/notifications/unread-count/{user_id}`

Get the count of unread notifications for a user.

**Path Parameters:**
- `user_id` (string): The user's ID

**Response:**
```json
{
  "user_id": "user_123",
  "unread_count": 3
}
```

## Dashboard

Access the interactive notifications dashboard at:
**`/api/ui-dashboard/notifications-dashboard-ui`**

Features:
- Create new notifications with custom user ID and content
- View all notifications or filter by user
- Mark individual notifications as read
- See unread count badge in real-time
- Auto-refreshes every 5 seconds
- Visual distinction between read and unread notifications

## Examples

**Create a notification:**
```bash
curl -X POST "http://localhost:8000/api/notifications/create" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "content": "Your order has been shipped!"}'
```

**Get all notifications:**
```bash
curl "http://localhost:8000/api/notifications/list"
```

**Get notifications for a specific user:**
```bash
curl "http://localhost:8000/api/notifications/list?user_id=user_123&limit=20"
```

**Mark a notification as read:**
```bash
curl -X POST "http://localhost:8000/api/notifications/mark-read/user_123/0"
```

**Get unread count:**
```bash
curl "http://localhost:8000/api/notifications/unread-count/user_123"
```

## Integration Examples

### Trigger notification on user action:
```python
from app.notifications.service import NotificationService

# After a successful order
NotificationService.create_notification(
    user_id=order.user_id,
    content=f"Your order #{order.id} has been confirmed!"
)
```

### Check unread notifications in a user profile endpoint:
```python
@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    unread_count = NotificationService.get_unread_count(user_id)
    return {
        "user_id": user_id,
        "unread_notifications": unread_count,
        # ... other profile data
    }
```

## Architecture

- **In-Memory Storage**: Current implementation uses a list for demo purposes
- **Thread-Safe**: Service methods can be called from multiple concurrent requests
- **Scalable Design**: Easy to replace with database persistence or message queue

## Future Enhancements

### WebSockets for Real-Time Delivery
Implement WebSocket connections to push notifications to connected clients instantly:

```python
from fastapi import WebSocket

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    # Stream notifications to this user in real-time
```

### Push Notifications
Integrate with services like Firebase Cloud Messaging (FCM) or Apple Push Notification service (APNs) for mobile notifications:

```python
import firebase_admin
from firebase_admin import messaging

def send_push_notification(user_id: str, notification: Notification):
    message = messaging.Message(
        notification=messaging.Notification(
            title="New Notification",
            body=notification.content
        ),
        token=get_user_device_token(user_id)
    )
    messaging.send(message)
```

### Notification Categories
Add filtering by notification type:

```python
class Notification(BaseModel):
    user_id: str
    content: str
    category: str  # 'message', 'system', 'alert', 'update'
    timestamp: datetime
    is_read: bool = False
```

### Database Persistence
Replace in-memory storage with SQLAlchemy models:

```python
class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    content = Column(Text)
    category = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
```

### Email Notifications
Send email notifications for important alerts:

```python
from app.notifications.email import send_email_notification

def create_notification(user_id: str, content: str, send_email: bool = False):
    notification = NotificationService.create_notification(user_id, content)
    if send_email:
        send_email_notification(user_id, notification)
    return notification
```

## Notes

- Current implementation stores notifications in memory (resets on restart)
- For production use, replace with database-backed persistence
- Consider implementing notification expiration/cleanup policies
- Add authentication middleware to ensure users can only access their own notifications
- Implement rate limiting to prevent notification spam
