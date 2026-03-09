#!/usr/bin/env pwsh
# Test PACK I Session Workflow

$BaseUrl = "http://localhost:4000"
$Headers = @{"Content-Type"="application/json"}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PACK I — Session Workflow Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Wait for server
Write-Host "Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test 1: Get current session (should be inactive)
Write-Host "`n1. Testing GET /core/go/session..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/core/go/session" -Method GET
    Write-Host "✓ Current session:" -ForegroundColor Green
    Write-Host "  Active: $($response.active)" -ForegroundColor Gray
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Start session
Write-Host "`n2. Testing POST /core/go/start_session..." -ForegroundColor Green
try {
    $body = @{"notes"="Testing PACK I session workflow"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseUrl/core/go/start_session" -Method POST -Headers $Headers -Body $body
    Write-Host "✓ Session started:" -ForegroundColor Green
    Write-Host "  Active: $($response.active)" -ForegroundColor Gray
    Write-Host "  Started at: $($response.started_at_utc)" -ForegroundColor Gray
    Write-Host "  Cone Band: $($response.cone_band)" -ForegroundColor Gray
    $sessionStartTime = $response.started_at_utc
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Get session (should be active now)
Write-Host "`n3. Testing GET /core/go/session (after start)..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/core/go/session" -Method GET
    Write-Host "✓ Current session:" -ForegroundColor Green
    Write-Host "  Active: $($response.active)" -ForegroundColor Green
    if ($response.active -eq $false) {
        Write-Host "  ⚠ WARNING: Session should be active!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 4: End session
Write-Host "`n4. Testing POST /core/go/end_session..." -ForegroundColor Green
try {
    $body = @{"notes"="Session completed successfully"} | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$BaseUrl/core/go/end_session" -Method POST -Headers $Headers -Body $body
    Write-Host "✓ Session ended:" -ForegroundColor Green
    Write-Host "  Active: $($response.active)" -ForegroundColor Gray
    Write-Host "  Started at: $($response.started_at_utc)" -ForegroundColor Gray
    Write-Host "  Ended at: $($response.ended_at_utc)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 5: Verify persistence
Write-Host "`n5. Checking persistence (data/go_session.json)..." -ForegroundColor Green
$sessionFile = "C:\dev\valhalla\data\go_session.json"
if (Test-Path $sessionFile) {
    $fileContent = Get-Content $sessionFile | ConvertFrom-Json
    Write-Host "✓ Session file exists:" -ForegroundColor Green
    Write-Host "  Active: $($fileContent.session.active)" -ForegroundColor Gray
    Write-Host "  Notes: $($fileContent.session.notes)" -ForegroundColor Gray
} else {
    Write-Host "✗ Session file not found at $sessionFile" -ForegroundColor Red
}

# Test 6: Check playbook still works
Write-Host "`n6. Testing PACK H playbook endpoint (coexistence)..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$BaseUrl/core/go/checklist" -Method GET
    Write-Host "✓ Playbook endpoint still works:" -ForegroundColor Green
    Write-Host "  Steps available: $($response.steps.Count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Session Workflow Test Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
