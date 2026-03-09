# Get current learning report
$base_url = "https://valhalla-api-ha6a.onrender.com"
$key = "a774e90bcc3de95f0513782e41fc454f"
$headers = @{ "X-API-Key" = $key }

Write-Host "`n=== LEARNING REPORT (POST-FILTER) ===" -ForegroundColor Cyan

$report = Invoke-RestMethod -Uri "$base_url/api/sandbox/learning/report" -Method GET -Headers $headers -TimeoutSec 10

Write-Host "`n📊 QUEUE METRICS" -ForegroundColor Cyan
Write-Host "Pending:   $($report.queue_metrics.pending) items" -ForegroundColor Yellow
Write-Host "Approved:  $($report.queue_metrics.approved) items" -ForegroundColor Green
Write-Host "Declined:  $($report.queue_metrics.declined) items" -ForegroundColor Yellow

Write-Host "`n⚖️ QUALITY METRICS" -ForegroundColor Cyan
Write-Host "Total Decided: $($report.quality_metrics.total_decided)" -ForegroundColor Gray
$approval_pct = [math]::Round($report.quality_metrics.approval_rate * 100, 1)
Write-Host "Approval Rate: $($approval_pct)%" -ForegroundColor $(if ($approval_pct -ge 75) { 'Green' } else { 'Yellow' })
$fp_pct = [math]::Round($report.quality_metrics.false_positive_rate * 100, 1)
Write-Host "False Positive Rate: $($fp_pct)%" -ForegroundColor $(if ($fp_pct -le 10) { 'Green' } else { 'Yellow' })
Write-Host "Status: $($report.quality_metrics.status)" -ForegroundColor Gray

Write-Host "`n🛡️ SAFETY METRICS" -ForegroundColor Cyan
Write-Host "False Positives: $($report.safety_metrics.false_positives)" -ForegroundColor Gray
Write-Host "FP Rate: $($fp_pct)%" -ForegroundColor Gray

Write-Host "`n📈 EVENT BREAKDOWN" -ForegroundColor Cyan
foreach ($event in $report.event_breakdown) {
    Write-Host "  $($event.event_type): $($event.count)" -ForegroundColor Gray
}

Write-Host "`n🧠 LEARNING STATUS" -ForegroundColor Cyan
Write-Host "Total Labels: $($report.learning_signals.total_labels)" -ForegroundColor Gray
Write-Host "Signal Strength: $($report.learning_signals.signal_strength)" -ForegroundColor Yellow

Write-Host "`n✅ PRE-QUEUE FILTER DEPLOYED" -ForegroundColor Green
Write-Host "Filter Status: ACTIVE" -ForegroundColor Green
Write-Host "Thresholds: MIN_PROFIT=\$25k, MIN_ROI=20%, MAX_RISK=15" -ForegroundColor Gray

# Show the impact
Write-Host "`n📉 FILTER IMPACT" -ForegroundColor Cyan
if ($report.event_breakdown) {
    $not_queued = $report.event_breakdown | Where-Object { $_.event_type -eq "OUTREACH_BLOCKED_NOT_QUEUED" } | Select-Object -First 1
    if ($not_queued) {
        Write-Host "Items Filtered Before Queue: $($not_queued.count) events" -ForegroundColor Green
    }
    $blocked_queued = $report.event_breakdown | Where-Object { $_.event_type -eq "OUTREACH_BLOCKED_QUEUED" } | Select-Object -First 1
    if ($blocked_queued) {
        Write-Host "Items That Passed Filter (Queued): $($blocked_queued.count) events" -ForegroundColor Green
    }
}

Write-Host "`n=== NEXT STEPS ===" -ForegroundColor Cyan
Write-Host "1. Monitor approval rate over next 24h (target: 75-90%)" -ForegroundColor Gray
Write-Host "2. Label 5-10 items from pending queue" -ForegroundColor Gray
Write-Host "3. Check scorecard tomorrow to see trend" -ForegroundColor Gray
Write-Host "4. Adjust thresholds after 20 items labeled" -ForegroundColor Gray
