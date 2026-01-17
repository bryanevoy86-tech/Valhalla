# Pack 15: Advanced User Analytics

This pack adds a small analytics surface for user activity: log actions and retrieve a user's activities, plus a tiny UI page.

## Endpoints
- `POST /api/analytics/log` — body: { user_id, action, metadata? }
- `GET /api/analytics/user-activity/{user_id}` — returns a list of recent activities

## Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"

# Log an action
Invoke-RestMethod -Method Post -Uri "$API/api/analytics/log" -ContentType 'application/json' -Body (@{ user_id='user_123'; action='login' } | ConvertTo-Json) | ConvertTo-Json -Depth 4

# Fetch user activity
Invoke-RestMethod -Method Get -Uri "$API/api/analytics/user-activity/user_123" | ConvertTo-Json -Depth 4
```

## UI
- `GET /api/ui-dashboard/analytics-dashboard-ui` — HTML page that fetches `/api/analytics/user-activity/{userId}` and renders a simple list.

## Notes
- This uses in-memory/log-line placeholders. To persist analytics, add a table and write in AnalyticsService.log_user_activity.
- For real-time streaming, a WebSocket can be added to push events to the UI.
