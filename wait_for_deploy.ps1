# Wait for Render deployment of commit b74c500 and test
Write-Host "`n=== Waiting for Render deployment ===" -ForegroundColor Cyan
Write-Host "Commit: b74c500" -ForegroundColor Yellow
Write-Host "Fixes applied:" -ForegroundColor Yellow
Write-Host "  1. Removed duplicate valhalla/ directory"
Write-Host "  2. Deleted root __init__.py creating valhalla package"
Write-Host "  3. Simplified main.py imports"
Write-Host "  4. Fixed .dockerignore patterns`n"

$API = "https://valhalla-api-ha6a.onrender.com"

Write-Host "Waiting 90 seconds for build + deploy..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

Write-Host "`n=== Testing API ===" -ForegroundColor Cyan

# Test health
try {
    Write-Host "Testing /api/health..." -NoNewline
    $health = Invoke-RestMethod -Uri "$API/api/health" -ErrorAction Stop
    Write-Host " ✓" -ForegroundColor Green
    $health | ConvertTo-Json -Compress
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# Test debug routes
Write-Host "`nTesting /debug/routes..." -NoNewline
try {
    $routes = Invoke-RestMethod -Uri "$API/debug/routes" -ErrorAction Stop
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "Pack Status:"
    Write-Host "  Intake (Pack-4): $($routes.intake_available)"
    Write-Host "  Contracts (Pack-5): $($routes.contracts_available)"
    Write-Host "  Total routes: $($routes.total_routes)"
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

Write-Host "`nDone!" -ForegroundColor Cyan
