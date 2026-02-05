#!/usr/bin/env powershell
<#
.SYNOPSIS
Contract Pipeline quick test script for local development.

.DESCRIPTION
Tests the complete contract pipeline workflow:
1. Seed templates
2. Create contract
3. Upload document
4. Transition states
5. Send for signature
6. Download document (presigned URL)
7. Check audit trail

.EXAMPLE
.\test_contract_pipeline.ps1 -BaseUrl "http://localhost:8000" -Verbose

.NOTES
Requires:
- Server running on specified BaseUrl
- PowerShell 5.0+
#>

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$Actor = "test-user"
)

function Test-Endpoint {
    param([string]$Method, [string]$Path, [object]$Body)
    
    $url = "$BaseUrl$Path"
    $headers = @{
        "Content-Type" = "application/json"
        "x-actor" = $Actor
    }
    
    $params = @{
        Uri = $url
        Method = $Method
        Headers = $headers
    }
    
    if ($Body) {
        $params["Body"] = ConvertTo-Json -Depth 10 $Body
    }
    
    try {
        Write-Host "[$Method] $Path" -ForegroundColor Cyan
        $response = Invoke-RestMethod @params
        Write-Host "✓ Success" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "✗ Failed: $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "`n=== Contract Pipeline Test Suite ===" -ForegroundColor Yellow
Write-Host "BaseUrl: $BaseUrl`n" -ForegroundColor Gray

# Test 1: Seed templates
Write-Host "`n[TEST 1] Seed Templates" -ForegroundColor Yellow
$seed = Test-Endpoint -Method "POST" -Path "/api/contracts/templates/seed"
if ($seed) {
    Write-Host "Created: $($seed.created) templates" -ForegroundColor Green
    $template_code = "ASSIGNMENT_AGREEMENT"
} else {
    Write-Host "Skipping remaining tests" -ForegroundColor Red
    exit 1
}

# Test 2: Create contract
Write-Host "`n[TEST 2] Create Contract" -ForegroundColor Yellow
$createPayload = @{
    template_code = $template_code
    title = "Test Assignment - Main St"
    deal_id = "TEST-DEAL-001"
    zone_id = "test-zone"
    merge_data = @{
        assignor_name = "Test Corp"
        assignee_name = "Buyer LLC"
        assignment_fee = 15000
    }
    parties = @(
        @{
            role = "ASSIGNOR"
            name = "Test Corp"
            email = "corp@test.com"
            must_sign = $true
        },
        @{
            role = "ASSIGNEE"
            name = "Buyer LLC"
            email = "buyer@test.com"
            must_sign = $true
        }
    )
    sign_provider = "SANDBOX"
}

$contract = Test-Endpoint -Method "POST" -Path "/api/contracts" -Body $createPayload
if ($contract) {
    Write-Host "Contract ID: $($contract.id)" -ForegroundColor Green
    $contract_id = $contract.id
    $state = $contract.state
    Write-Host "Initial State: $state" -ForegroundColor Green
} else {
    Write-Host "Skipping remaining tests" -ForegroundColor Red
    exit 1
}

# Test 3: Upload document
Write-Host "`n[TEST 3] Upload Draft Document" -ForegroundColor Yellow
$testPdfPath = "$env:TEMP\test_contract.pdf"
if (-not (Test-Path $testPdfPath)) {
    # Create minimal PDF for testing
    $pdfBytes = [System.Text.Encoding]::UTF8.GetBytes("%PDF-1.4`n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj xref 0 4 0000000000 65535 f 0000000009 00000 n 0000000058 00000 n 0000000115 00000 n trailer<</Size 4/Root 1 0 R>>startxref 190 %%EOF")
    [System.IO.File]::WriteAllBytes($testPdfPath, $pdfBytes)
}

$uploadUrl = "$BaseUrl/api/contracts/$contract_id/upload?kind=DRAFT"
try {
    Write-Host "[POST] /api/contracts/$contract_id/upload" -ForegroundColor Cyan
    $upload = Invoke-RestMethod -Uri $uploadUrl -Method "POST" -Form @{
        file = Get-Item $testPdfPath
    } -Headers @{"x-actor" = $Actor}
    
    Write-Host "✓ Success" -ForegroundColor Green
    Write-Host "Document ID: $($upload.doc_id)" -ForegroundColor Green
    $doc_id = $upload.doc_id
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    Write-Host "Skipping remaining tests" -ForegroundColor Red
    exit 1
}

# Test 4: Check state is still DRAFT
Write-Host "`n[TEST 4] Verify Contract State" -ForegroundColor Yellow
$getUrl = "$BaseUrl/api/contracts/$contract_id"
try {
    Write-Host "[GET] /api/contracts/$contract_id" -ForegroundColor Cyan
    $current = Invoke-RestMethod -Uri $getUrl -Method "GET"
    Write-Host "✓ Current State: $($current.state)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test 5: Transition to APPROVED_FOR_SIGNATURE
Write-Host "`n[TEST 5] Approve for Signature" -ForegroundColor Yellow
$approvePayload = @{
    target = "APPROVED_FOR_SIGNATURE"
    note = "Document reviewed and ready"
}
$approved = Test-Endpoint -Method "POST" -Path "/api/contracts/$contract_id/state" -Body $approvePayload
if ($approved) {
    Write-Host "New State: $($approved.state)" -ForegroundColor Green
}

# Test 6: Send for signature
Write-Host "`n[TEST 6] Send for Signature" -ForegroundColor Yellow
$sendPayload = @{
    subject = "Please review and sign"
    message = "Contract is ready for signature"
}
$envelope = Test-Endpoint -Method "POST" -Path "/api/contracts/$contract_id/send" -Body $sendPayload
if ($envelope) {
    Write-Host "Envelope ID: $($envelope.envelope_id)" -ForegroundColor Green
    Write-Host "Provider Envelope ID: $($envelope.provider_envelope_id)" -ForegroundColor Green
    Write-Host "Status: $($envelope.status)" -ForegroundColor Green
}

# Test 7: Download document (presigned URL)
Write-Host "`n[TEST 7] Download Document (Presigned URL)" -ForegroundColor Yellow
$download = Test-Endpoint -Method "GET" -Path "/api/contracts/$contract_id/documents/$doc_id/download"
if ($download) {
    Write-Host "URL (expires in $($download.expires_seconds)s):" -ForegroundColor Green
    Write-Host $download.url -ForegroundColor Gray
}

# Test 8: Check audit trail
Write-Host "`n[TEST 8] Audit Trail" -ForegroundColor Yellow
$events = Test-Endpoint -Method "GET" -Path "/api/contracts/$contract_id/events"
if ($events) {
    Write-Host "Total Events: $($events.Count)" -ForegroundColor Green
    foreach ($event in $events) {
        Write-Host "  - $($event.event_type) by $($event.actor) at $($event.created_at)" -ForegroundColor Gray
    }
}

Write-Host "`n=== All Tests Complete ===" -ForegroundColor Green
