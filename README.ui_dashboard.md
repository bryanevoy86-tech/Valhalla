# Admin Dashboard with Metrics Visualization — Pack 10

This pack adds a simple admin dashboard UI that visualizes runtime metrics (RPS, error rate, p50 latency) using Chart.js and your existing `/api/metrics` data source.

Endpoints
- `GET /api/ui-dashboard/metrics-dashboard` → JSON metrics (requests_per_sec, error_rate, p50_latency, totals)
- `GET /api/ui-dashboard/metrics-dashboard-ui` → HTML dashboard page
- `GET /api/admin/metrics` → JSON metrics (admin convenience)

Quick test (PowerShell)
```powershell
$API = "https://<your-render-service>.onrender.com"
# JSON for charts
Invoke-RestMethod -Method Get -Uri "$API/api/ui-dashboard/metrics-dashboard" | ConvertTo-Json -Depth 4
# HTML page
Invoke-RestMethod -Method Get -Uri "$API/api/ui-dashboard/metrics-dashboard-ui"
```

Notes
- The dashboard fetches `/api/ui-dashboard/metrics-dashboard` every 2 seconds and updates charts.
- For restricted environments, you can gate `/api/admin/metrics` behind an admin key if desired.
- This UI is intentionally lightweight; for WeWeb, you can call the JSON endpoint directly and render charts natively there.