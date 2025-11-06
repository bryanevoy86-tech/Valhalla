# Pack 22: Activity Tracking and User Metrics

## Overview

This pack introduces activity tracking and user metrics to monitor and analyze user actions across the system. The data captured can be used for performance optimization, security monitoring, and audit logging.

## Features

- **Activity Recording**: Track user actions with timestamps, action types, and contextual details
- **Activity Retrieval**: Query recent activities with configurable limits
- **Dashboard Integration**: Visual interface for recording and viewing user activities
- **In-Memory Storage**: Fast access with sliding window (last 1000 activities retained)

## Endpoints

### POST `/api/metrics/track`

Record a user activity event.

**Query Parameters:**
- `user_id` (string, required): User identifier
- `action` (string, required): Action type (e.g., 'login', 'view', 'update')
- `details` (string, optional): Additional context about the activity

**Response:**
```json
{
  "user_id": "user_123",
  "action": "login",
  "timestamp": "2025-11-05T10:30:00.123456",
  "details": "Successful login"
}
```

### GET `/api/metrics/activities`

Retrieve recent user activities.

**Query Parameters:**
- `limit` (integer, optional, default=100): Maximum number of activities to return

**Response:**
```json
[
  {
    "user_id": "user_123",
    "action": "login",
    "timestamp": "2025-11-05T10:30:00.123456",
    "details": "Successful login"
  },
  {
    "user_id": "user_456",
    "action": "view",
    "timestamp": "2025-11-05T10:31:00.789012",
    "details": "Viewed dashboard"
  }
]
```

## Dashboard

The metrics dashboard at `/api/ui-dashboard/metrics-dashboard-ui` now includes an Activity Tracking section where you can:

- Record new activities with custom user ID, action, and details
- View recent activities in a scrollable log
- Refresh the activity list on demand

## Examples

**Record a login activity:**
```bash
curl -X POST "http://localhost:8000/api/metrics/track?user_id=user_123&action=login&details=Successful+login"
```

**Record a view action:**
```bash
curl -X POST "http://localhost:8000/api/metrics/track?user_id=user_456&action=view&details=Viewed+analytics+page"
```

**Get recent activities:**
```bash
curl "http://localhost:8000/api/metrics/activities?limit=20"
```

## Notes

- Current implementation uses in-memory storage with a sliding window of 1000 activities
- For production use, replace with database-backed persistence in `ActivityService`
- Activities are thread-safe and can be recorded from multiple concurrent requests
- Consider adding indexes and retention policies when moving to database storage

## Future Enhancements

- Database persistence for long-term activity retention
- Activity filtering by user, action type, or time range
- Aggregated metrics (activities per user, most common actions, etc.)
- Integration with security monitoring and alerting systems
- Export capabilities for compliance and audit reporting
