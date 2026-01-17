# Pack 19: Advanced Logging and Auditing

This pack adds a minimal logging and audit surface to track user actions.

## Endpoints
- POST `/api/logging/log` — body `{ "user_id": "...", "action": "...", "details": "..." }` returns a LogEntry

## Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"

Invoke-RestMethod -Method Post -Uri "$API/api/logging/log" -ContentType 'application/json' -Body (@{ user_id = 'user_123'; action = 'login'; details = 'Successful login' } | ConvertTo-Json) | ConvertTo-Json -Depth 4
```

## UI
- GET `/api/ui-dashboard/logging-dashboard-ui` — small page to submit and display a log entry

## Notes
- This writes to Python's `logging` at INFO. For production, route to external sinks (CloudWatch, Loggly, ELK), add persistence, and implement rotation/retention.
