# Final test after fffd0cb deployment - wrapper script approach
$API = "https://valhalla-api-ha6a.onrender.com"
$KEY = "2af3d998e1b7e2ca882291732aa40dd9"

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   Valhalla API Deployment Test (fffd0cb)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`nFix Applied:" -ForegroundColor Yellow
Write-Host "  • Created start.py wrapper script" -ForegroundColor White
Write-Host "  • Directly imports app object (bypasses uvicorn CLI)" -ForegroundColor White
Write-Host "  • Explicitly sets sys.path before import" -ForegroundColor White
Write-Host "  • Removed all valhalla namespace references`n" -ForegroundColor White

Write-Host "Waiting 2 minutes for Render build + deploy..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

Write-Host "`n────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host " API Tests" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────────────────" -ForegroundColor Gray

# Test 1: Health check
Write-Host "`n[1/3] GET /api/health" -NoNewline
try {
    $health = Invoke-RestMethod -Uri "$API/api/health" -TimeoutSec 15 -ErrorAction Stop
    Write-Host " ✓ SUCCESS" -ForegroundColor Green
    Write-Host "      Response: $($health | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n⚠ Deployment may still be in progress. Try again in 1-2 minutes." -ForegroundColor Yellow
    exit 1
}

# Test 2: Debug routes
Write-Host "`n[2/3] GET /debug/routes" -NoNewline
try {
    $routes = Invoke-RestMethod -Uri "$API/debug/routes" -TimeoutSec 15 -ErrorAction Stop
    Write-Host " ✓ SUCCESS" -ForegroundColor Green
    Write-Host "      Total routes: $($routes.total_routes)" -ForegroundColor Gray
    Write-Host "`n      Router Status:" -ForegroundColor Gray
    Write-Host "        Intake (Pack-4):    " -NoNewline -ForegroundColor Gray
    if ($routes.intake_available) { Write-Host "✓ Available" -ForegroundColor Green } else { Write-Host "✗ Missing" -ForegroundColor Red }
    Write-Host "        Contracts (Pack-5): " -NoNewline -ForegroundColor Gray
    if ($routes.contracts_available) { Write-Host "✓ Available" -ForegroundColor Green } else { Write-Host "✗ Missing" -ForegroundColor Red }
    Write-Host "        Buyers:             " -NoNewline -ForegroundColor Gray
    if ($routes.buyers_available) { Write-Host "✓ Available" -ForegroundColor Green } else { Write-Host "✗ Missing" -ForegroundColor Red }
    Write-Host "        Deals:              " -NoNewline -ForegroundColor Gray
    if ($routes.deals_available) { Write-Host "✓ Available" -ForegroundColor Green } else { Write-Host "✗ Missing" -ForegroundColor Red }
    Write-Host "        Match:              " -NoNewline -ForegroundColor Gray
    if ($routes.match_available) { Write-Host "✓ Available" -ForegroundColor Green } else { Write-Host "✗ Missing" -ForegroundColor Red }
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Sample Pack-4 endpoint
Write-Host "`n[3/3] GET /api/intake/leads (Pack-4)" -NoNewline
try {
    $headers = @{ "X-API-Key" = $KEY }
    $leads = Invoke-RestMethod -Uri "$API/api/intake/leads" -Headers $headers -TimeoutSec 15 -ErrorAction Stop
    Write-Host " ✓ SUCCESS" -ForegroundColor Green
    Write-Host "      Leads count: $($leads.Count)" -ForegroundColor Gray
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    Write-Host "      Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " 🎉 Deployment test complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
