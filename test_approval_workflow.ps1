#!/usr/bin/env powershell
# Test the approval workflow

$api_key = "a774e90bcc3de95f0513782e41fc454f"
$base_url = "https://valhalla-api-ha6a.onrender.com"
$headers = @{"X-API-Key" = $api_key}

Write-Host "=== STEP 1: Queue a test email (should be queued for approval in SANDBOX) ===" -ForegroundColor Cyan
$body = @{
    to = "workflow_test@example.com"
    subject = "Approval Workflow Test"
    body_html = "<p>This is a test email for the approval workflow</p>"
    body_text = "This is a test email for the approval workflow"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "$base_url/api/notify/email" -Method POST -Headers $headers -ContentType "application/json" -Body $body -UseBasicParsing
Write-Host "Response Code: $($response.StatusCode)" -ForegroundColor Green
$queue_response = $response.Content | ConvertFrom-Json
Write-Host "Queue Response:"
$queue_response | ConvertTo-Json

Write-Host "`n=== STEP 2: List pending approvals ===" -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "$base_url/api/approvals/pending" -Method GET -Headers $headers -UseBasicParsing
Write-Host "Response Code: $($response.StatusCode)" -ForegroundColor Green
$pending = $response.Content | ConvertFrom-Json
Write-Host "Pending Actions:"
$pending | ConvertTo-Json

if ($pending -and $pending.Count -gt 0) {
    $action_id = $pending[0].id
    Write-Host "`nFound pending action ID: $action_id" -ForegroundColor Yellow
    
    Write-Host "`n=== STEP 3: Approve the pending action ===" -ForegroundColor Cyan
    $response = Invoke-WebRequest -Uri "$base_url/api/approvals/$action_id/approve" -Method POST -Headers $headers -UseBasicParsing
    Write-Host "Response Code: $($response.StatusCode)" -ForegroundColor Green
    $approve_response = $response.Content | ConvertFrom-Json
    Write-Host "Approval Response:"
    $approve_response | ConvertTo-Json
    
    Write-Host "`n=== STEP 4: Check activity feed ===" -ForegroundColor Cyan
    $response = Invoke-WebRequest -Uri "$base_url/api/sandbox/activity" -Method GET -Headers $headers -UseBasicParsing
    Write-Host "Response Code: $($response.StatusCode)" -ForegroundColor Green
    $activity = $response.Content | ConvertFrom-Json
    Write-Host "Recent Activity:"
    $activity | ConvertTo-Json
} else {
    Write-Host "No pending actions found!" -ForegroundColor Red
}
