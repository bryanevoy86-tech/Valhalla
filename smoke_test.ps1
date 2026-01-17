#!/usr/bin/env powershell
# Valhalla Phase 2 Smoke Test (PowerShell version)
# Tests all Phase 2 integration points end-to-end

$BaseURL = "http://localhost:8000"
$Province = "ON"
$Market = "Toronto"

function Test-Endpoint {
    param([string]$Name, [string]$Method, [string]$Endpoint, [hashtable]$Data)
    
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    
    try {
        if ($Method -eq "POST" -and $Data) {
            $json = $Data | ConvertTo-Json -Depth 5
            Write-Host "POST $Endpoint" -ForegroundColor Gray
            Write-Host "Payload: $($json.Substring(0, [Math]::Min(200, $json.Length)))..." -ForegroundColor Gray
            $response = curl.exe -s -X POST "$BaseURL$Endpoint" -H "Content-Type: application/json" -d $json
        } else {
            Write-Host "GET $Endpoint" -ForegroundColor Gray
            $response = curl.exe -s "$BaseURL$Endpoint"
        }
        
        if ($response) {
            Write-Host "[PASS] Response received" -ForegroundColor Green
            Write-Host $response.Substring(0, [Math]::Min(300, $response.Length))
            return $true
        } else {
            Write-Host "[FAIL] No response" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "[FAIL] Error: $_" -ForegroundColor Red
        return $false
    }
}

Write-Host "Valhalla Phase 2 Smoke Test (PowerShell)" -ForegroundColor Yellow
Write-Host "Base URL: $BaseURL" -ForegroundColor Yellow
Write-Host "Province: $Province, Market: $Market" -ForegroundColor Yellow

$results = @()

# Test 1: Runbook status
$results += @{
    Name = "1) Governance Runbook Status"
    Pass = Test-Endpoint "Runbook Status" "GET" "/api/governance/runbook/status"
}

# Test 2: Market Policy - Create/Enable for Province
$results += @{
    Name = "2) Market Policy - Upsert"
    Pass = Test-Endpoint "Upsert Market Policy" "POST" "/api/deals/offers/policies/upsert?province=$Province&market=$Market&enabled=true&max_arv_multiplier=0.70&default_assignment_fee=10000&default_fees_buffer=2500&changed_by=test&reason=smoke_test"
}

# Test 3: Market Policy - Check effective rules
$results += @{
    Name = "3) Market Policy - Effective Rules"
    Pass = Test-Endpoint "Effective Market Policy" "GET" "/api/governance/market/effective?province=$Province&market=$Market"
}

# Test 4: Lead-to-Deal Flow
$flowPayload = @{
    phone_number = "4165551234"
    first_name = "Test"
    last_name = "Lead"
    property_address = "123 Bloor St, Toronto, ON"
    property_city = "Toronto"
    property_province = "ON"
    owner_name = "Bryan Test"
    correlation_id = "smoke_test_$(Get-Random)"
}
$results += @{
    Name = "4) Lead-to-Deal Flow"
    Pass = Test-Endpoint "Lead-to-Deal Flow" "POST" "/api/flow/lead-to-deal" -Data $flowPayload
}

# Test 5: Offer Computation
$results += @{
    Name = "5) Offer Computation"
    Pass = Test-Endpoint "Compute Offer" "POST" "/api/deals/offers/compute?province=$Province&market=$Market&arv=650000&repairs=35000&correlation_id=smoke_test_offer"
}

# Test 6: Buyer Liquidity Score
$results += @{
    Name = "6) Buyer Liquidity Scoring"
    Pass = Test-Endpoint "Liquidity Score" "GET" "/api/buyers/liquidity/score?province=$Province&market=$Market&property_type=SFR"
}

# Test 7: Follow-up Ladder
$results += @{
    Name = "7) Follow-up Ladder Status"
    Pass = Test-Endpoint "Follow-up Due Tasks" "GET" "/api/followups/due?limit=20"
}

# Test 8: KPI Trail
$results += @{
    Name = "8) KPI Trail and Monitoring"
    Pass = Test-Endpoint "KPI State" "GET" "/api/governance/kpi/trail"
}

# Summary
Write-Host "`n`n=== SUMMARY ===" -ForegroundColor Yellow
$passed = ($results | Where-Object { $_.Pass }).Count
$total = $results.Count

$results | ForEach-Object {
    $status = if ($_.Pass) { "[PASS]" } else { "[FAIL]" }
    $color = if ($_.Pass) { "Green" } else { "Red" }
    Write-Host "$status $($_.Name)" -ForegroundColor $color
}

Write-Host "`nTotal: $passed/$total passed" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })

if ($passed -eq $total) {
    Write-Host "`n=== Phase 2 Integration Validated ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n=== Some tests failed ===" -ForegroundColor Red
    exit 1
}
