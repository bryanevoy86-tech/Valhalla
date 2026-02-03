#!/usr/bin/env powershell
# Analyze the 5 decided items to understand decline reasons

$api_key = "a774e90bcc3de95f0513782e41fc454f"
$base_url = "https://valhalla-api-ha6a.onrender.com"
$headers = @{"X-API-Key" = $api_key}

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "ANALYSIS: 5 DECIDED ITEMS (Approved vs Declined)" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

# Get all actions (approved + declined)
$response = Invoke-WebRequest -Uri "$base_url/api/approvals/decided?limit=1000" -Method GET -Headers $headers -UseBasicParsing
$decided = $response.Content | ConvertFrom-Json

Write-Host "`nAPPROVED ITEMS:" -ForegroundColor Green
$approved = $decided | Where-Object {$_.status -eq "APPROVED"}
$i = 1
foreach ($item in $approved) {
    Write-Host "`n  [$i] APPROVED" -ForegroundColor Green
    Write-Host "    ID: $($item.id)"
    Write-Host "    Type: $($item.action_type)"
    Write-Host "    Target: $($item.target)" -ForegroundColor Gray
    Write-Host "    Subject: $($item.subject)"
    Write-Host "    Created: $($item.created_at)"
    if ($item.payload) {
        Write-Host "    Preview: $($item.preview_text.Substring(0, [Math]::Min(80, $item.preview_text.Length)))..." -ForegroundColor Gray
    }
    $i++
}

Write-Host "`n`nDECLINED ITEMS (Flag with category):" -ForegroundColor Red
$declined = $decided | Where-Object {$_.status -eq "DECLINED"}
$i = 1
foreach ($item in $declined) {
    Write-Host "`n  [$i] DECLINED" -ForegroundColor Red
    Write-Host "    ID: $($item.id)"
    Write-Host "    Type: $($item.action_type)"
    Write-Host "    Target: $($item.target)" -ForegroundColor Gray
    Write-Host "    Subject: $($item.subject)"
    Write-Host "    Created: $($item.created_at)"
    if ($item.payload) {
        Write-Host "    Preview: $($item.preview_text.Substring(0, [Math]::Min(80, $item.preview_text.Length)))..." -ForegroundColor Gray
    }
    Write-Host "`n    Why declined? (enter one):" -ForegroundColor Yellow
    Write-Host "    - PRICE (profit too low)" -ForegroundColor Gray
    Write-Host "    - RISK (risk too high)" -ForegroundColor Gray
    Write-Host "    - DATA_MISSING (incomplete info)" -ForegroundColor Gray
    Write-Host "    - NOT_MY_STRATEGY (wrong fit)" -ForegroundColor Gray
    Write-Host "    - OTHER" -ForegroundColor Gray
    $i++
}

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "KEY INSIGHTS" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

Write-Host "`nSample of what got queued:" -ForegroundColor Yellow
$decidedEmail = $decided | Where-Object {$_.action_type -eq "OUTREACH_EMAIL"} | Select-Object -First 1
if ($decidedEmail) {
    Write-Host "  Email recipient: $($decidedEmail.target)" -ForegroundColor Gray
    Write-Host "  Status: $($decidedEmail.status)" -ForegroundColor Gray
}

Write-Host "`nNext: Categorize the 2 declined items above, then we'll tighten the gate." -ForegroundColor Cyan
Write-Host "Once we know (PRICE/RISK/DATA/STRATEGY), we adjust the pre-queue filter." -ForegroundColor Gray

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
