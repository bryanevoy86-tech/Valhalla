#!/usr/bin/env powershell
# Test the new learning report endpoints

$api_key = "a774e90bcc3de95f0513782e41fc454f"
$base_url = "https://valhalla-api-ha6a.onrender.com"
$headers = @{"X-API-Key" = $api_key}

Write-Host "`n" + ("="*70) -ForegroundColor Cyan
Write-Host "SANDBOX LEARNING REPORT - NEW ENDPOINTS" -ForegroundColor Cyan
Write-Host ("="*70) -ForegroundColor Cyan

# TEST 1: Full learning report
Write-Host "`n[TEST 1] GET /api/sandbox/learning/report" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base_url/api/sandbox/learning/report" -Method GET -Headers $headers -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    $report = $response.Content | ConvertFrom-Json
    
    Write-Host "`nQueue Metrics:" -ForegroundColor Cyan
    Write-Host "  Pending:  $($report.queue.pending)"
    Write-Host "  Approved: $($report.queue.approved)"
    Write-Host "  Declined: $($report.queue.declined)"
    
    Write-Host "`nQuality Metrics:" -ForegroundColor Cyan
    Write-Host "  Total Decided:  $($report.quality.total_decided)"
    Write-Host "  Approval Rate:  $($report.quality.approval_rate)"
    Write-Host "  Status:         $($report.quality.interpretation)"
    
    Write-Host "`nSafety Metrics:" -ForegroundColor Cyan
    Write-Host "  False Positives: $($report.safety.false_positives)"
    Write-Host "  FP Rate:        $($report.safety.fp_rate)"
    Write-Host "  Status:         $($report.safety.status)"
    
    Write-Host "`nEvent Breakdown:" -ForegroundColor Cyan
    Write-Host "  Total Events: $($report.events.total)"
    foreach ($event in $report.events.breakdown.PSObject.Properties) {
        Write-Host "    - $($event.Name): $($event.Value)"
    }
    
    Write-Host "`nLearning Signals:" -ForegroundColor Cyan
    Write-Host "  Total Labels:   $($report.learning.total_labels)"
    Write-Host "  Signal Strength: $($report.learning.signal_strength)"
    Write-Host "  Recommendation: $($report.learning.recommendation)"
    
    Write-Host "`nSystem Health:" -ForegroundColor Cyan
    Write-Host "  Queue Size:     $($report.system_health.queue_size)"
    Write-Host "  Safety Status:  $($report.system_health.safety_status)"
    Write-Host "  Learning:       $($report.system_health.learning_active)"
    
} catch {
    Write-Host "ERROR: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

# TEST 2: Scorecard (simplified view)
Write-Host "`n[TEST 2] GET /api/sandbox/learning/scorecard" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base_url/api/sandbox/learning/scorecard" -Method GET -Headers $headers -UseBasicParsing
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    $scorecard = $response.Content | ConvertFrom-Json
    
    Write-Host "`nDaily Scorecard ($($scorecard.date)):" -ForegroundColor Cyan
    foreach ($metric in $scorecard.metrics.PSObject.Properties) {
        Write-Host "  $($metric.Name.PadRight(25)): $($metric.Value)"
    }
    
    Write-Host "`nStatus:       $($scorecard.status)" -ForegroundColor Cyan
    Write-Host "Learning:     $($scorecard.learning_recommendation)" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

Write-Host "`n" + ("="*70) -ForegroundColor Green
Write-Host "NEXT STEPS FOR EFFECTIVE LEARNING:" -ForegroundColor Green
Write-Host ("="*70) -ForegroundColor Green
Write-Host "`n1. Label 20 items consistently:" -ForegroundColor Yellow
Write-Host "   - From /api/approvals/pending, add labels with POST /api/sandbox/labels"
Write-Host "   - Use APPROVE, REJECT, NEEDS_INFO based on your decision"
Write-Host "`n2. Check this report daily:" -ForegroundColor Yellow
Write-Host "   - Monitor approval_rate (should trend up if learning)"
Write-Host "   - Watch false_positive_rate (should stay near 0)"
Write-Host "   - Track labels_collected (target: 20+)"
Write-Host "`n3. Use scorecard for email alerts:" -ForegroundColor Yellow
Write-Host "   - Endpoint responds with simplified metrics for dashboards"
Write-Host "   - Can be called by Daily Ops email to show progress"
Write-Host "`n" + ("="*70) -ForegroundColor Cyan
