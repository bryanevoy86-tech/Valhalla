# Pack 11: Real-time Alerts with Thresholds

This pack adds real-time alerting based on metrics thresholds for error rate and latency. Alerts are generated when metrics exceed acceptable levels.

## Thresholds
- **Error rate > 10%** → triggers `error_rate_high` alert
- **p50 Latency > 1.0s** → triggers `high_latency` alert

## Endpoints
- `GET /api/alerts` → JSON array of active alerts
- `GET /api/ui-dashboard/alerts-dashboard` → JSON array (same as above, for UI)
- `GET /api/ui-dashboard/alerts-dashboard-ui` → HTML page with auto-refresh

## Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"

# Check for alerts (JSON)
Invoke-RestMethod -Method Get -Uri "$API/api/alerts" | ConvertTo-Json -Depth 4

# View alerts dashboard UI
Invoke-RestMethod -Method Get -Uri "$API/api/ui-dashboard/alerts-dashboard-ui"
```

## Notes
- Alerts are computed on-the-fly from current in-process metrics (no persistence).
- If no thresholds exceeded, returns an empty array `[]`.
- The HTML dashboard auto-refreshes every 3 seconds and displays "No alerts" when all metrics are within acceptable bounds.
- For persistent alert logs, consider writing alerts to the `integrity_events` table or a dedicated `alerts` table.

## Optional enhancements
- Add WebSocket endpoint for real-time push notifications (no polling).
- Configurable thresholds via settings or API.
- Integrate with external notification systems (Slack, PagerDuty, email).
