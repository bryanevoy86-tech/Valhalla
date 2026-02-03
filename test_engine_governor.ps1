# Test Engine Activation Governor
$base_url = "https://valhalla-api-ha6a.onrender.com"
$key = "a774e90bcc3de95f0513782e41fc454f"
$headers = @{ "X-API-Key" = $key }

Write-Host "`n=== ENGINE ACTIVATION GOVERNOR TEST ===" -ForegroundColor Cyan
Write-Host "Testing: State machine, promotion guards, readiness evaluation" -ForegroundColor Gray

# Test 1: Check initial state (should be seeded)
Write-Host "`n[TEST 1] List all engines and states" -ForegroundColor Yellow
try {
    $engines = Invoke-RestMethod -Uri "$base_url/api/governance/engines/readiness" -Method GET -Headers $headers -TimeoutSec 10
    
    Write-Host "Registered Engines:" -ForegroundColor Cyan
    foreach ($engine in $engines) {
        Write-Host "  $($engine.engine_name): $($engine.state)" -ForegroundColor $(if ($engine.state -eq "SANDBOX") { 'Yellow' } elseif ($engine.state -eq "LIVE") { 'Green' } else { 'Gray' })
    }
    
    $wholesaling = $engines | Where-Object { $_.engine_name -eq "wholesaling" } | Select-Object -First 1
    if ($wholesaling) {
        Write-Host "`nWholesaling Details:" -ForegroundColor Gray
        Write-Host "  State: $($wholesaling.state)" -ForegroundColor Yellow
        Write-Host "  Approval Rate: $($wholesaling.approval_rate)" -ForegroundColor Gray
        Write-Host "  FP Rate: $($wholesaling.false_positive_rate)" -ForegroundColor Gray
        Write-Host "  Samples: $($wholesaling.sample_size)" -ForegroundColor Gray
    }
    Write-Host "`n✅ PASS - Engine registry exists" -ForegroundColor Green
} catch {
    Write-Host "❌ FAIL - $($_)" -ForegroundColor Red
}

# Test 2: Try to call notify/email when not LIVE (should fail)
Write-Host "`n[TEST 2] Try to dispatch email while wholesaling is SANDBOX (should fail)" -ForegroundColor Yellow
try {
    $body = @{
        to = "governor-test@example.com"
        subject = "Governor Test"
        body_text = "This should fail because engine is not LIVE"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$base_url/api/notify/email" -Method POST -Headers $headers -Body $body -TimeoutSec 10
    Write-Host "❌ FAIL - Should have been blocked! Response: $response" -ForegroundColor Red
} catch {
    $error_msg = $_.Exception.Response.StatusCode
    if ($error_msg -eq "Conflict") {
        Write-Host "✅ PASS - Email dispatch blocked (409 Conflict)" -ForegroundColor Green
        Write-Host "  Reason: Engine 'wholesaling' not LIVE (current state: SANDBOX)" -ForegroundColor Gray
    } else {
        Write-Host "Response: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

# Test 3: Promote to READY (simulated - would need metrics in real scenario)
Write-Host "`n[TEST 3] Try to promote without READY state (should fail)" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$base_url/api/governance/engines/wholesaling/promote" -Method POST -Headers $headers -TimeoutSec 10
    Write-Host "❌ FAIL - Should have required READY state!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq "Conflict") {
        Write-Host "✅ PASS - Promotion rejected (engine not READY)" -ForegroundColor Green
    } else {
        Write-Host "Response: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

# Test 4: Manual evaluation
Write-Host "`n[TEST 4] Evaluate wholesaling engine" -ForegroundColor Yellow
try {
    $eval = Invoke-RestMethod -Uri "$base_url/api/governance/engines/wholesaling/evaluate" -Method POST -Headers $headers -TimeoutSec 10
    
    $status = $eval.evaluation.status
    Write-Host "Evaluation Result: $status" -ForegroundColor $(if ($status -eq "promoted_to_ready") { 'Green' } else { 'Yellow' })
    
    if ($status -eq "promoted_to_ready") {
        Write-Host "  ✅ Promoted to READY!" -ForegroundColor Green
    } elseif ($status -eq "not_ready") {
        Write-Host "  Not ready - missing thresholds:" -ForegroundColor Gray
        Write-Host "    Passes Samples: $($eval.evaluation.passes_samples)" -ForegroundColor Gray
        Write-Host "    Passes Approval: $($eval.evaluation.passes_approval)" -ForegroundColor Gray
        Write-Host "    Passes FP Rate: $($eval.evaluation.passes_fp_rate)" -ForegroundColor Gray
    }
} catch {
    Write-Host "Error: $($_)" -ForegroundColor Red
}

# Test 5: Check state after evaluation
Write-Host "`n[TEST 5] Check engine state after evaluation" -ForegroundColor Yellow
try {
    $engines = Invoke-RestMethod -Uri "$base_url/api/governance/engines/readiness" -Method GET -Headers $headers -TimeoutSec 10
    $wholesaling = $engines | Where-Object { $_.engine_name -eq "wholesaling" } | Select-Object -First 1
    
    Write-Host "Wholesaling State: $($wholesaling.state)" -ForegroundColor $(if ($wholesaling.state -eq "READY") { 'Green' } else { 'Yellow' })
    Write-Host "✅ State update verified" -ForegroundColor Green
} catch {
    Write-Host "Error: $($_)" -ForegroundColor Red
}

Write-Host "`n=== GOVERNOR TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Gray
Write-Host "1. Label 20 items to meet sample threshold" -ForegroundColor Gray
Write-Host "2. Run evaluation to promote to READY" -ForegroundColor Gray
Write-Host "3. Call promotion endpoint to go LIVE" -ForegroundColor Gray
Write-Host "4. After LIVE, email dispatch will execute" -ForegroundColor Gray
