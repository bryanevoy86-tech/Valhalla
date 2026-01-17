# Pack 13: Custom Metrics Dashboards for Different User Roles

This pack introduces role-based dashboard configurations so Admins and Viewers can see tailored metric sets.

## API
- `GET /api/metrics/dashboard/admin`
- `GET /api/metrics/dashboard/viewer`

Response example
```json
{
  "role": "admin",
  "metrics": ["total_errors", "requests_per_sec", "p50_latency", "error_rate"],
  "last_updated": "2025-11-05T12:34:56.123456"
}
```

## UI
The existing metrics dashboard page now includes a small role selector and a "Load" button that fetches `GET /api/metrics/dashboard/{role}` and shows the configured keys.

## PowerShell quick check
```powershell
$API = "https://<your-render-service>.onrender.com"
Invoke-RestMethod -Method Get -Uri "$API/api/metrics/dashboard/admin" | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Get -Uri "$API/api/metrics/dashboard/viewer" | ConvertTo-Json -Depth 4
```
