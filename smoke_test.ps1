#!/usr/bin/env powershell
# Valhalla Local Dev Smoke Test
# Validates Floor Control Plane + system health

$BaseURL = "http://127.0.0.1:8010"
$ApiKey = $env:VALHALLA_API_KEY

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "VALHALLA LOCAL DEV SMOKE TEST" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Base URL: $BaseURL" -ForegroundColor Gray
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

$passCount = 0
$failCount = 0

# Test 1: Health Check
Write-Host "`n[TEST 1/3] Health Endpoint" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "$BaseURL/health" -TimeoutSec 3 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "[PASS]" -ForegroundColor Green
        $json = $response.Content | ConvertFrom-Json
        Write-Host "  Status: $($json.status)" -ForegroundColor Green
        Write-Host "  Heimdall: $($json.heimdall)" -ForegroundColor Green
        $passCount++
    } else {
        Write-Host "[FAIL] Status $($response.StatusCode)" -ForegroundColor Red
        $failCount++
    }
} catch {
    Write-Host "[FAIL] Connection error: $_" -ForegroundColor Red
    $failCount++
}

# Test 2: System Selftest
Write-Host "`n[TEST 2/3] System Selftest" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "$BaseURL/api/system/selftest" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "[PASS]" -ForegroundColor Green
        $json = $response.Content | ConvertFrom-Json
        Write-Host "  OK: $($json.ok)" -ForegroundColor Green
        Write-Host "  Routes Found: $($json.route_count)" -ForegroundColor Green
        $passCount++
    } else {
        Write-Host "[FAIL] Status $($response.StatusCode)" -ForegroundColor Red
        $failCount++
    }
} catch {
    Write-Host "[FAIL] Connection error: $_" -ForegroundColor Red
    $failCount++
}

# Test 3: Floor Control Routes Accessible
Write-Host "`n[TEST 3/3] Floor Control Routes Registered" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest "$BaseURL/__routes" -TimeoutSec 3 -UseBasicParsing
    $routes = $response.Content
    
    $floorRoutes = @(
        "/api/governance/floor/engines/upsert",
        "/api/governance/floor/revenue/record",
        "/api/governance/floor/targets/upsert",
        "/api/governance/floor/trajectory/month"
    )
    
    $allFound = $true
    foreach ($route in $floorRoutes) {
        if ($routes -match [regex]::Escape($route)) {
            Write-Host "  [OK] $route" -ForegroundColor Green
        } else {
            Write-Host "  [MISSING] $route" -ForegroundColor Red
            $allFound = $false
        }
    }
    
    if ($allFound) {
        $passCount++
    } else {
        $failCount++
    }
} catch {
    Write-Host "[FAIL] Connection error: $_" -ForegroundColor Red
    $failCount++
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed: $passCount/3" -ForegroundColor $(if ($passCount -eq 3) { "Green" } else { "Yellow" })
Write-Host "Failed: $failCount/3" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

if ($passCount -eq 3) {
    Write-Host "`n[SUCCESS] All tests passed - Local dev environment is healthy" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[WARNING] Some tests failed - Check server and connectivity" -ForegroundColor Yellow
    exit 1
}
