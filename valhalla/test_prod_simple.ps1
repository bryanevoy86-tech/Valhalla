# Simple production test for Pack-4 and Pack-5
$API = "https://valhalla-api-ha6a.onrender.com/api"
$KEY = "test123"
$H = @{ "X-API-Key" = $KEY; "Content-Type" = "application/json" }

Write-Host "`n=== Testing Production Deployment ===" -ForegroundColor Cyan

# Test 1: Health
Write-Host "`n1. Health Check..." -NoNewline
$health = Invoke-RestMethod -Uri "$API/health" -TimeoutSec 20
Write-Host " OK - v$($health.version)" -ForegroundColor Green

# Test 2: Check if intake endpoint exists
Write-Host "`n2. Testing Pack-4 intake endpoint..." -NoNewline
try {
    $lead = '{"source":"prod_test","name":"Test User","email":"test@example.com","region":"Winnipeg"}'
    $r = Invoke-RestMethod -Uri "$API/intake/leads" -Method POST -Headers $H -Body $lead -TimeoutSec 20
    Write-Host " OK - Lead ID: $($r.id)" -ForegroundColor Green
    $leadId = $r.id
    
    # Test normalize
    Write-Host "   Normalizing lead..." -NoNewline
    $n = Invoke-RestMethod -Uri "$API/intake/leads/$leadId/normalize" -Method POST -Headers $H -TimeoutSec 20
    Write-Host " OK - Deal ID: $($n.deal_id)" -ForegroundColor Green
} catch {
    Write-Host " FAILED - $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "   Endpoint not available. Render may not have deployed yet." -ForegroundColor Yellow
}

# Test 3: Check if contracts endpoint exists  
Write-Host "`n3. Testing Pack-5 contracts endpoint..." -NoNewline
try {
    $tmpl = '{"name":"Test Template","body_text":"Test contract content"}'
    $t = Invoke-RestMethod -Uri "$API/contracts/templates" -Method POST -Headers $H -Body $tmpl -TimeoutSec 20
    Write-Host " OK - Template ID: $($t.id)" -ForegroundColor Green
} catch {
    Write-Host " FAILED - $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "   Endpoint not available. Render may not have deployed yet." -ForegroundColor Yellow
}

Write-Host "`n" -ForegroundColor Cyan
