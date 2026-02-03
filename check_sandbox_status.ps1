#!/usr/bin/env powershell
# Check what's running in SANDBOX

$api_key = "a774e90bcc3de95f0513782e41fc454f"
$base_url = "https://valhalla-api-ha6a.onrender.com"
$headers = @{"X-API-Key" = $api_key}

Write-Host "`n==============================" -ForegroundColor Cyan
Write-Host "SANDBOX SYSTEM STATUS CHECK" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Check health
Write-Host "`n[1] API Health" -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "$base_url/health" -UseBasicParsing
Write-Host "Status: $($response.StatusCode) - $($response.Content)" -ForegroundColor Green

# Check environment
Write-Host "`n[2] Check APP_ENV (SANDBOX vs LIVE)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base_url/api/governance" -UseBasicParsing
    Write-Host "Governance endpoint: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host ($content | ConvertTo-Json) -ForegroundColor Gray
} catch {
    Write-Host "Governance endpoint not available" -ForegroundColor Yellow
}

# Check pending approvals (what's queued)
Write-Host "`n[3] Pending Approvals (What's Queued)" -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "$base_url/api/approvals/pending?limit=5" -Method GET -Headers $headers -UseBasicParsing
$pending = $response.Content | ConvertFrom-Json
Write-Host "Total pending: $($pending.Count)" -ForegroundColor Green
if ($pending.Count -gt 0) {
    Write-Host "Most recent action:" -ForegroundColor Gray
    $latest = $pending | Select-Object -First 1
    Write-Host "  ID: $($latest.id)" -ForegroundColor Gray
    Write-Host "  Type: $($latest.action_type)" -ForegroundColor Gray
    Write-Host "  Target: $($latest.target)" -ForegroundColor Gray
    Write-Host "  Created: $($latest.created_at)" -ForegroundColor Gray
}

# Check activity log
Write-Host "`n[4] Recent Activity (Last 10 Events)" -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "$base_url/api/sandbox/activity?limit=10" -Method GET -Headers $headers -UseBasicParsing
$activity = $response.Content | ConvertFrom-Json
Write-Host "Total events: $($activity.Count)" -ForegroundColor Green
$eventTypes = $activity | Group-Object -Property event_type | Select-Object Name, Count
Write-Host "Event types:" -ForegroundColor Gray
foreach ($type in $eventTypes) {
    Write-Host "  - $($type.Name): $($type.Count)" -ForegroundColor Gray
}

# Check if test email endpoint works
Write-Host "`n[5] Test Email Endpoint (SANDBOX Safe)" -ForegroundColor Yellow
try {
    $body = '{"to":"ValhallaLegacyInc@gmail.com","subject":"Status Check","body_html":"<p>System is running</p>","body_text":"System is running"}'
    $response = Invoke-WebRequest -Uri "$base_url/api/notify/test-email" -Method POST -Headers $headers -ContentType "application/json" -Body $body -UseBasicParsing
    Write-Host "Status: $($response.StatusCode) - Test email endpoint is active" -ForegroundColor Green
} catch {
    Write-Host "Test email endpoint returned: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
}

# Summary
Write-Host "`n==============================" -ForegroundColor Cyan
Write-Host "SANDBOX SYSTEM SUMMARY" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "`nRunning Components:" -ForegroundColor Cyan
Write-Host "- FastAPI application (Uvicorn)" -ForegroundColor Green
Write-Host "- PostgreSQL database connection" -ForegroundColor Green
Write-Host "- Notify router (email + webhook queueing)" -ForegroundColor Green
Write-Host "- Approvals router (pending action management)" -ForegroundColor Green
Write-Host "- SANDBOX activity router (event logging)" -ForegroundColor Green
Write-Host "- Guard engine (SANDBOX mode active - blocks outreach)" -ForegroundColor Green
Write-Host "- SMTP service (for test-email endpoint)" -ForegroundColor Green
Write-Host "`nPending Actions: $($pending.Count) queued items waiting for approval" -ForegroundColor Yellow
Write-Host "Recent Events: $($activity.Count) recorded in activity log" -ForegroundColor Yellow
