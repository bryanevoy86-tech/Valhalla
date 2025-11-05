# Quick validation after the valhalla package removal fix
$API = "https://valhalla-api-ha6a.onrender.com"
$KEY = "2af3d998e1b7e2ca882291732aa40dd9"

Write-Host "`n=== Testing Valhalla API after fix ===" -ForegroundColor Cyan
Write-Host "Waiting for deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test 1: Health endpoint
Write-Host "`n1. Testing /api/health..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod -Uri "$API/api/health" -Method Get -ErrorAction Stop
    Write-Host "✓ Health check passed" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
}

# Test 2: Debug routes
Write-Host "`n2. Testing /debug/routes..." -ForegroundColor Cyan
try {
    $routes = Invoke-RestMethod -Uri "$API/debug/routes" -Method Get -ErrorAction Stop
    Write-Host "✓ Debug routes accessible" -ForegroundColor Green
    Write-Host "Available routers:" -ForegroundColor Yellow
    Write-Host "  - Intake (Pack-4): $($routes.intake_available)"
    Write-Host "  - Contracts (Pack-5): $($routes.contracts_available)"
    Write-Host "  - Buyers: $($routes.buyers_available)"
    Write-Host "  - Deals: $($routes.deals_available)"
    Write-Host "  - Match: $($routes.match_available)"
    Write-Host "  - Notify: $($routes.notify_available)"
    Write-Host "  - Grants: $($routes.grants_available)"
    Write-Host "  Total routes: $($routes.total_routes)"
} catch {
    Write-Host "✗ Debug routes failed: $_" -ForegroundColor Red
}

# Test 3: Pack-4 Intake endpoint
Write-Host "`n3. Testing Pack-4 /api/intake/leads..." -ForegroundColor Cyan
try {
    $headers = @{
        "X-API-Key" = $KEY
    }
    $intake = Invoke-RestMethod -Uri "$API/api/intake/leads" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "✓ Pack-4 Intake endpoint working" -ForegroundColor Green
    Write-Host "  Leads returned: $($intake.Count)"
} catch {
    Write-Host "✗ Pack-4 failed: $_" -ForegroundColor Red
}

# Test 4: Pack-5 Contracts endpoint
Write-Host "`n4. Testing Pack-5 /api/contracts/templates..." -ForegroundColor Cyan
try {
    $headers = @{
        "X-API-Key" = $KEY
    }
    $contracts = Invoke-RestMethod -Uri "$API/api/contracts/templates" -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "✓ Pack-5 Contracts endpoint working" -ForegroundColor Green
    Write-Host "  Templates returned: $($contracts.Count)"
} catch {
    Write-Host "✗ Pack-5 failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Test complete ===" -ForegroundColor Cyan
