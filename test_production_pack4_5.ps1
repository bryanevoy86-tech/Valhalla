# Test Pack-4 and Pack-5 endpoints on production
$API = "https://valhalla-api-ha6a.onrender.com/api"
$KEY = "test123"
$headers = @{ "X-API-Key" = $KEY; "Content-Type" = "application/json" }

Write-Host "`n=== Testing Valhalla Production Deployment ===" -ForegroundColor Cyan
Write-Host "API: $API`n" -ForegroundColor Gray

# Test 1: Health
Write-Host "1. Health Check..." -NoNewline
try {
    $health = Invoke-RestMethod -Uri "$API/health" -Method GET -TimeoutSec 20
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "   Version: $($health.version), App: $($health.app)" -ForegroundColor Gray
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Debug Routes (check what's registered)
Write-Host "`n2. Checking registered routes..." -NoNewline
try {
    $routes = Invoke-RestMethod -Uri "https://valhalla-api-ha6a.onrender.com/debug/routes" -Method GET -TimeoutSec 20
    $intakeRoutes = $routes | Where-Object { $_ -like "*intake*" }
    $contractRoutes = $routes | Where-Object { $_ -like "*contract*" }
    
    if ($intakeRoutes.Count -gt 0 -or $contractRoutes.Count -gt 0) {
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "   Pack-4/5 routes found:" -ForegroundColor Gray
        $intakeRoutes | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
        $contractRoutes | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
    } else {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "   No Pack-4/5 routes found. Deployment may not be complete." -ForegroundColor Yellow
        Write-Host "   Sample routes:" -ForegroundColor Gray
        $routes | Select-Object -First 10 | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
        exit 1
    }
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Pack-4 - Create Lead
Write-Host "`n3. Pack-4: Create Lead Intake..." -NoNewline
try {
    $lead = @{
        source = "production_test"
        name = "Test Production"
        email = "test.prod@example.com"
        region = "Winnipeg"
        property_type = "single family"
        price = 299000
        beds = 3
        baths = 2
    } | ConvertTo-Json
    
    $leadResp = Invoke-RestMethod -Uri "$API/intake/leads" -Method POST -Headers $headers -Body $lead -TimeoutSec 20
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "   Lead ID: $($leadResp.id), Status: $($leadResp.status)" -ForegroundColor Gray
    $leadId = $leadResp.id
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Response.StatusCode) - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 4: Pack-4 - Normalize Lead
Write-Host "`n4. Pack-4: Normalize Lead to Deal..." -NoNewline
try {
    $normalizeResp = Invoke-RestMethod -Uri "$API/intake/leads/$leadId/normalize" -Method POST -Headers $headers -TimeoutSec 20
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "   Lead ID: $($normalizeResp.lead_id), Deal ID: $($normalizeResp.deal_id)" -ForegroundColor Gray
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Response.StatusCode) - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Pack-4 - Queue Notification
Write-Host "`n5. Pack-4: Queue Email Notification..." -NoNewline
try {
    $email = @{
        to = "test@example.com"
        subject = "Test Notification"
        body_text = "This is a test notification"
    } | ConvertTo-Json
    
    $notifyResp = Invoke-RestMethod -Uri "$API/notify/email" -Method POST -Headers $headers -Body $email -TimeoutSec 20
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "   Notification ID: $($notifyResp.id), Status: $($notifyResp.status)" -ForegroundColor Gray
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Response.StatusCode) - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Pack-5 - Create Contract Template
Write-Host "`n6. Pack-5: Create Contract Template..." -NoNewline
try {
    $template = @{
        name = "Test Assignment Template"
        version = "1.0"
        body_text = "Assignment Agreement`nSeller: {{seller_name}}`nBuyer: {{buyer_name}}`nPrice: ${{price}}"
    } | ConvertTo-Json
    
    $tmplResp = Invoke-RestMethod -Uri "$API/contracts/templates" -Method POST -Headers $headers -Body $template -TimeoutSec 20
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "   Template ID: $($tmplResp.id), Name: $($tmplResp.name)" -ForegroundColor Gray
    $templateId = $tmplResp.id
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Response.StatusCode) - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 7: Pack-5 - Generate Contract
Write-Host "`n7. Pack-5: Generate Contract PDF..." -NoNewline
try {
    $generate = @{
        template_id = $templateId
        filename = "test_contract_{{deal_id}}.pdf"
        data = @{
            seller_name = "Jane Seller"
            buyer_name = "ABC Capital"
            price = 299000
            deal_id = 42
        }
    } | ConvertTo-Json
    
    $contractResp = Invoke-RestMethod -Uri "$API/contracts/generate" -Method POST -Headers $headers -Body $generate -TimeoutSec 20
    Write-Host " ✓" -ForegroundColor Green
    Write-Host "   Contract ID: $($contractResp.id), Filename: $($contractResp.filename)" -ForegroundColor Gray
    $contractId = $contractResp.id
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Response.StatusCode) - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 8: Pack-5 - Fetch PDF
Write-Host "`n8. Pack-5: Fetch Contract PDF..." -NoNewline
try {
    $pdfResp = Invoke-WebRequest -Uri "$API/contracts/records/$contractId/pdf" -Headers $headers -TimeoutSec 20
    if ($pdfResp.Headers.'Content-Type' -like "*pdf*") {
        Write-Host " ✓" -ForegroundColor Green
        Write-Host "   PDF Size: $($pdfResp.Content.Length) bytes" -ForegroundColor Gray
    } else {
        Write-Host " ?" -ForegroundColor Yellow
        Write-Host "   Unexpected content type: $($pdfResp.Headers.'Content-Type')" -ForegroundColor Yellow
    }
} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Response.StatusCode) - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Cyan
