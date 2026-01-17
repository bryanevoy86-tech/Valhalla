# Pack 9.1: Metrics Endpoint + Counters

This pack adds lightweight in-process counters and augments the existing `/api/metrics` endpoint to report both DB counts and runtime performance metrics for easy consumption from WeWeb.

What you get
- Runtime counters: `requests_per_sec`, `error_rate`, `p50_latency`, `total_requests`, `total_errors`
- Existing DB counts are preserved: `research_sources`, `research_docs`, `telemetry_events`, `capital_intake_records`, `builder_tasks`, `playbooks`
- Middleware automatically tracks every request's latency and success/failure

Endpoints
- GET `/api/metrics` → JSON payload with counters and table counts

Quick test
```powershell
# Replace with your Render base URL
$API = "https://<your-render-service>.onrender.com"

# Fetch metrics (JSON)
Invoke-RestMethod -Method Get -Uri "$API/api/metrics" | ConvertTo-Json -Depth 4
```

Notes
- `requests_per_sec` is the average since process start (simple and stable for small services).
- `p50_latency` is the median of the last 1000 requests.
- For Prometheus scraping, you can add a separate `/metrics/prometheus` endpoint using `prometheus_client` if desired.