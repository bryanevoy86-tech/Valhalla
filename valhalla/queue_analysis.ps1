#!/usr/bin/env powershell
# Simple test to show current queue and analyzed items

$api_key = "a774e90bcc3de95f0513782e41fc454f"
$base_url = "https://valhalla-api-ha6a.onrender.com"
$headers = @{"X-API-Key" = $api_key}

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "QUEUE ANALYSIS: What Needs Gate Tuning" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

# Get current pending items
Write-Host "`nCurrent PENDING items in queue:" -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri "$base_url/api/approvals/pending?limit=10" -Method GET -Headers $headers -UseBasicParsing
$pending = $response.Content | ConvertFrom-Json

if ($pending.Count -gt 0) {
    $index = 0
    foreach ($item in $pending) {
        $index++
        Write-Host "`n  Item $index`: $($item.target)" -ForegroundColor Cyan
        Write-Host "    Type: $($item.action_type)"
        Write-Host "    Subject: $($item.subject)"
        Write-Host "    Queued: $($item.created_at)" -ForegroundColor Gray
        if ($item.reason -match "profit|roi|risk") {
            Write-Host "    Gate Info: $($item.reason)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  (No pending items)" -ForegroundColor Gray
}

Write-Host "`n" + ("="*70) -ForegroundColor Green
Write-Host "NEXT STEP: Pre-Queue Filter" -ForegroundColor Green
Write-Host ("="*70) -ForegroundColor Green

Write-Host "`nTo improve approval rate fast, we add a pre-queue filter:" -ForegroundColor Yellow
Write-Host "  - Only queue if: profit >= 20000 AND roi >= 20 AND risk <= 15"
Write-Host "  - Otherwise: log OUTREACH_BLOCKED_NOT_QUEUED instead" -ForegroundColor Gray
Write-Host "`nThis reduces junk in the queue before it reaches you." -ForegroundColor Gray
Write-Host "Expected result: approval rate should jump from 60% to 75%+" -ForegroundColor Gray

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
