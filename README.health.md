# Pack 14: Automated System Health Check & Recovery

This pack adds a lightweight, on-demand system health check and a dashboard. It composes a health status from basic probes and metrics and returns a structured JSON response.

## Endpoints
- `GET /api/system-health` — Structured JSON health snapshot (no conflict with existing /api/health)
- `GET /api/ui-dashboard/health-dashboard` — JSON for dashboard
- `GET /api/ui-dashboard/health-dashboard-ui` — HTML dashboard page that auto-refreshes

## Example (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"
Invoke-RestMethod -Method Get -Uri "$API/api/system-health" | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Get -Uri "$API/api/ui-dashboard/health-dashboard" | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Get -Uri "$API/api/ui-dashboard/health-dashboard-ui"
```

## Notes
- Checks currently include: service up, placeholder server resources, and metrics error-rate (<25%).
- Recovery action is a placeholder (`"Recovery triggered: no-op"`) returned when unhealthy; extend to restart services or notify on-call as needed.
- If you want a scheduled checker, we can add a background task or an external cron to hit the endpoint and act on results.
