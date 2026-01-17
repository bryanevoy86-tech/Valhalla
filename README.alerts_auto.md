# Pack 12: Automated Alert Handling

This pack introduces automated responses to alerts. When defined thresholds are exceeded (e.g., error rate or latency), you can trigger actions like sending email notifications.

## Endpoints
- `POST /api/alerts/handle` — Accepts an AlertOut and performs the configured action, returning an AlertResponseOut.

## Example (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"
Invoke-RestMethod -Method Post -Uri "$API/api/alerts/handle" -ContentType 'application/json' -Body (@{
  alert_type = 'high_latency'
  message    = 'High latency detected!'
  triggered_at = (Get-Date).ToString('s')
} | ConvertTo-Json) | ConvertTo-Json -Depth 4
```

## Configuration
Set environment variables to enable email notifications:
- `ALERTS_FROM_EMAIL` (e.g., noreply@example.com)
- `ALERTS_TO_EMAIL` (e.g., admin@example.com)
- `ALERTS_SMTP_HOST` (e.g., smtp.example.com)
- `ALERTS_SMTP_PORT` (default: 25)

If SMTP is not configured or fails, the action returns status `failed` with the error message; otherwise `success`.

## Notes
- Alerts are currently handled synchronously and only demonstrate an email action for `high_latency`.
- Extend `AlertsService.handle_alert` to add actions like Slack, PagerDuty, or service restarts.
- UI button added on the Alerts Dashboard to trigger the example action for quick checks.
