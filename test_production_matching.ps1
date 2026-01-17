# Test Pack-3 Matching Engine on Production
$API = "https://valhalla-api-ha6a.onrender.com/api"
$KEY = $env:HEIMDALL_BUILDER_API_KEY
if (-not $KEY) {
    Write-Host "Error: Set HEIMDALL_BUILDER_API_KEY environment variable" -ForegroundColor Red
    exit 1
}

$headers = @{
    "X-API-Key" = $KEY
    "Content-Type" = "application/json"
}

Write-Host "`n=== Testing Buyer Matching Engine on Production ===" -ForegroundColor Cyan

# Test 1: Create Buyer
Write-Host "`n[1/6] Creating buyer..." -ForegroundColor Yellow
$buyer = @{
    name = "Winnipeg SFH Buyer"
    regions = "Winnipeg,CA-MB"
    property_types = "SFH,Duplex"
    min_price = 100000
    max_price = 350000
    min_beds = 3
    min_baths = 1
    tags = "garage,corner lot"
} | ConvertTo-Json

try {
    $buyerResult = Invoke-RestMethod -Uri "$API/buyers" -Method POST -Headers $headers -Body $buyer -TimeoutSec 30
    Write-Host "✅ Buyer created: ID=$($buyerResult.id), Name=$($buyerResult.name)" -ForegroundColor Green
    $buyerId = $buyerResult.id
} catch {
    Write-Host "❌ Failed to create buyer: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: List Buyers
Write-Host "`n[2/6] Listing active buyers..." -ForegroundColor Yellow
try {
    $buyers = Invoke-RestMethod -Uri "$API/buyers?active=true" -Method GET -Headers $headers -TimeoutSec 30
    Write-Host "✅ Found $($buyers.Count) active buyer(s)" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to list buyers: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Create Deal
Write-Host "`n[3/6] Creating deal..." -ForegroundColor Yellow
$deal = @{
    headline = "SFH in Transcona with garage"
    region = "Winnipeg"
    property_type = "SFH"
    price = 289000
    beds = 3
    baths = 1
    notes = "solid bones, corner lot"
} | ConvertTo-Json

try {
    $dealResult = Invoke-RestMethod -Uri "$API/deals" -Method POST -Headers $headers -Body $deal -TimeoutSec 30
    Write-Host "✅ Deal created: ID=$($dealResult.id), Headline=$($dealResult.headline)" -ForegroundColor Green
    $dealId = $dealResult.id
} catch {
    Write-Host "❌ Failed to create deal: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 4: Match Deal → Buyers
Write-Host "`n[4/6] Computing matches: deal → buyers..." -ForegroundColor Yellow
$matchRequest = @{
    deal_id = $dealId
    min_score = 0.25
    limit = 10
} | ConvertTo-Json

try {
    $matchResult = Invoke-RestMethod -Uri "$API/match/compute" -Method POST -Headers $headers -Body $matchRequest -TimeoutSec 30
    Write-Host "✅ Found $($matchResult.total) matching buyer(s)" -ForegroundColor Green
    if ($matchResult.hits.Count -gt 0) {
        $topHit = $matchResult.hits[0]
        Write-Host "   Top match: $($topHit.buyer_name) (Score: $([math]::Round($topHit.score, 3)))" -ForegroundColor Cyan
        Write-Host "   Reasons: $($topHit.reasons -join ', ')" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Failed to compute deal→buyers match: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 5: Match Buyer → Deals
Write-Host "`n[5/6] Computing matches: buyer → deals..." -ForegroundColor Yellow
$matchRequest = @{
    buyer_id = $buyerId
    min_score = 0.25
    limit = 10
} | ConvertTo-Json

try {
    $matchResult = Invoke-RestMethod -Uri "$API/match/compute" -Method POST -Headers $headers -Body $matchRequest -TimeoutSec 30
    Write-Host "✅ Found $($matchResult.total) matching deal(s)" -ForegroundColor Green
    if ($matchResult.hits.Count -gt 0) {
        $topHit = $matchResult.hits[0]
        Write-Host "   Top match: $($topHit.headline) (Score: $([math]::Round($topHit.score, 3)))" -ForegroundColor Cyan
        Write-Host "   Reasons: $($topHit.reasons -join ', ')" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Failed to compute buyer→deals match: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 6: Sweep Job
Write-Host "`n[6/6] Running sweep job..." -ForegroundColor Yellow
try {
    $sweepResult = Invoke-RestMethod -Uri "$API/jobs/match/sweep?limit=5" -Method GET -Headers $headers -TimeoutSec 30
    Write-Host "✅ Sweep completed successfully" -ForegroundColor Green
    Write-Host "   Deals evaluated: $($sweepResult.deals_evaluated)" -ForegroundColor Cyan
    Write-Host "   Buyers evaluated: $($sweepResult.buyers_evaluated)" -ForegroundColor Cyan
    Write-Host "   Deals with top hits: $($sweepResult.deals_with_top_hits)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to run sweep job: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== ✅ All 6 tests passed! Pack-3 is live on production! ===" -ForegroundColor Green
