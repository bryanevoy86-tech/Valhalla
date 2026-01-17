# Monitor Render deployment and test when ready
$API = "https://valhalla-api-ha6a.onrender.com/api"
$KEY = $env:HEIMDALL_BUILDER_API_KEY
if (-not $KEY) {
    Write-Host "❌ Error: Set HEIMDALL_BUILDER_API_KEY environment variable" -ForegroundColor Red
    exit 1
}

$headers = @{
    "X-API-Key" = $KEY
    "Content-Type" = "application/json"
}

Write-Host "`n=== Monitoring Render Deployment ===" -ForegroundColor Cyan
Write-Host "Commit: d60664e (Pack-3: Buyer Matching Engine)" -ForegroundColor Gray
Write-Host "Waiting for new endpoints to become available...`n" -ForegroundColor Gray

$maxAttempts = 20
$attempt = 0
$deployed = $false

while ($attempt -lt $maxAttempts -and -not $deployed) {
    $attempt++
    Write-Host "[$attempt/$maxAttempts] Checking deployment status..." -ForegroundColor Yellow
    
    try {
        # Test if buyers endpoint exists
        $response = Invoke-RestMethod -Uri "$API/buyers?active=true" -Method GET -Headers $headers -TimeoutSec 10 -ErrorAction Stop
        $deployed = $true
        Write-Host "✅ Deployment complete! New endpoints are live." -ForegroundColor Green
        break
    } catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "   Still deploying... (endpoint not found)" -ForegroundColor Gray
        } elseif ($_.Exception.Response.StatusCode -eq 401) {
            Write-Host "❌ Authentication failed! Check HEIMDALL_BUILDER_API_KEY" -ForegroundColor Red
            exit 1
        } else {
            Write-Host "   Waiting... ($($_.Exception.Message))" -ForegroundColor Gray
        }
        
        if ($attempt -lt $maxAttempts) {
            Start-Sleep -Seconds 15
        }
    }
}

if (-not $deployed) {
    Write-Host "`n❌ Deployment timeout. Check Render dashboard for status." -ForegroundColor Red
    Write-Host "Dashboard: https://dashboard.render.com" -ForegroundColor Cyan
    exit 1
}

# Run full test suite
Write-Host "`n=== Running Production Tests ===" -ForegroundColor Cyan
& "$PSScriptRoot\test_production_matching.ps1"
