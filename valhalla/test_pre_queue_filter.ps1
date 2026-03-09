# Test Pre-Queue Quality Filter
$base_url = "https://valhalla-api-ha6a.onrender.com"
$key = "a774e90bcc3de95f0513782e41fc454f"
$headers = @{ "X-API-Key" = $key; "Content-Type" = "application/json" }

Write-Host "`n=== PRE-QUEUE FILTER TEST ===" -ForegroundColor Cyan
Write-Host "Testing quality gates: MIN_PROFIT=25000, MIN_ROI=20%, MAX_RISK=15" -ForegroundColor Gray

# Test 1: High-quality item (should PASS gate)
Write-Host "`n[TEST 1] HIGH-QUALITY item (profit=50k, roi=35%, risk=8)" -ForegroundColor Yellow
$body = @{
    url = "https://webhook.example.com/notify"
    payload = @{
        expected_profit = 50000
        roi_percentage = 35
        risk_score = 8
        deal_id = "test-hq-001"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$base_url/api/notify/webhook" -Method POST -Headers $headers -Body $body -TimeoutSec 10
Write-Host "Queued: $($response.queued_for_approval)" -ForegroundColor Green

# Test 2: Low-profit item (should FAIL gate)
Write-Host "`n[TEST 2] LOW-PROFIT item (profit=10k, roi=25%, risk=8)" -ForegroundColor Yellow
$body = @{
    url = "https://webhook.example.com/notify"
    payload = @{
        expected_profit = 10000
        roi_percentage = 25
        risk_score = 8
        deal_id = "test-lp-001"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$base_url/api/notify/webhook" -Method POST -Headers $headers -Body $body -TimeoutSec 10
Write-Host "Queued: $($response.queued_for_approval) | Reason: $($response.reason)" -ForegroundColor Green

# Test 3: Low-ROI item
Write-Host "`n[TEST 3] LOW-ROI item (profit=30k, roi=10%, risk=8)" -ForegroundColor Yellow
$body = @{
    url = "https://webhook.example.com/notify"
    payload = @{
        expected_profit = 30000
        roi_percentage = 10
        risk_score = 8
        deal_id = "test-lr-001"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$base_url/api/notify/webhook" -Method POST -Headers $headers -Body $body -TimeoutSec 10
Write-Host "Queued: $($response.queued_for_approval) | Reason: $($response.reason)" -ForegroundColor Green

# Test 4: High-risk item
Write-Host "`n[TEST 4] HIGH-RISK item (profit=40k, roi=30%, risk=25)" -ForegroundColor Yellow
$body = @{
    url = "https://webhook.example.com/notify"
    payload = @{
        expected_profit = 40000
        roi_percentage = 30
        risk_score = 25
        deal_id = "test-hr-001"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$base_url/api/notify/webhook" -Method POST -Headers $headers -Body $body -TimeoutSec 10
Write-Host "Queued: $($response.queued_for_approval) | Reason: $($response.reason)" -ForegroundColor Green

# Test 5: Borderline item
Write-Host "`n[TEST 5] BORDERLINE item (profit=25k, roi=20%, risk=15)" -ForegroundColor Yellow
$body = @{
    url = "https://webhook.example.com/notify"
    payload = @{
        expected_profit = 25000
        roi_percentage = 20
        risk_score = 15
        deal_id = "test-bl-001"
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$base_url/api/notify/webhook" -Method POST -Headers $headers -Body $body -TimeoutSec 10
Write-Host "Queued: $($response.queued_for_approval)" -ForegroundColor Green

Write-Host "`n=== EXPECTED RESULTS ===" -ForegroundColor Cyan
Write-Host "Test 1: True  (passes all gates)" -ForegroundColor Gray
Write-Host "Test 2: False (profit too low)" -ForegroundColor Gray
Write-Host "Test 3: False (roi too low)" -ForegroundColor Gray
Write-Host "Test 4: False (risk too high)" -ForegroundColor Gray
Write-Host "Test 5: True  (at thresholds)" -ForegroundColor Gray

Write-Host "`n=== FILTER ACTIVE ===" -ForegroundColor Cyan
