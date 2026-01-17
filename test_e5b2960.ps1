# Test after e5b2960 deployment
$API = "https://valhalla-api-ha6a.onrender.com"
$KEY = "2af3d998e1b7e2ca882291732aa40dd9"

Write-Host "`n=== Waiting for Render deployment (e5b2960) ===" -ForegroundColor Cyan
Write-Host "Key fix: Direct Python import bypasses uvicorn's string loader`n" -ForegroundColor Yellow

Write-Host "Waiting 2 minutes for build + deploy..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

Write-Host "`n=== Testing API ===" -ForegroundColor Cyan

try {
    Write-Host "GET /api/health..." -NoNewline
    $result = Invoke-RestMethod -Uri "$API/api/health" -TimeoutSec 10
    Write-Host " ✓ SUCCESS!" -ForegroundColor Green
    $result | ConvertTo-Json
    
    Write-Host "`nGET /debug/routes..." -NoNewline
    $routes = Invoke-RestMethod -Uri "$API/debug/routes" -TimeoutSec 10
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "`nRouter Status:"
    Write-Host "  Intake (Pack-4): $($routes.intake_available)" -ForegroundColor $(if($routes.intake_available){"Green"}else{"Red"})
    Write-Host "  Contracts (Pack-5): $($routes.contracts_available)" -ForegroundColor $(if($routes.contracts_available){"Green"}else{"Red"})
    Write-Host "  Total routes: $($routes.total_routes)"
    
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`nAPI may still be deploying. Check Render logs."
}

Write-Host "`nDone!" -ForegroundColor Cyan
