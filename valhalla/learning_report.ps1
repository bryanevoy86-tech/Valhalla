#!/usr/bin/env powershell
# Query learning metrics via the running API

$api_key = "a774e90bcc3de95f0513782e41fc454f"
$base_url = "https://valhalla-api-ha6a.onrender.com"
$headers = @{"X-API-Key" = $api_key}

Write-Host "`n" + ("="*60) -ForegroundColor Cyan
Write-Host "SANDBOX LEARNING METRICS - LIVE REPORT" -ForegroundColor Cyan
Write-Host ("="*60) -ForegroundColor Cyan

# Get pending actions to show status breakdown
Write-Host "`n[1] PENDING ACTIONS BY STATUS" -ForegroundColor Yellow
Write-Host ("-"*60) -ForegroundColor Gray

$response = Invoke-WebRequest -Uri "$base_url/api/approvals/pending?limit=1000" -Method GET -Headers $headers -UseBasicParsing
$allActions = $response.Content | ConvertFrom-Json

$pending = ($allActions | Where-Object {$_.status -eq 'PENDING'} | Measure-Object).Count
$approved = ($allActions | Where-Object {$_.status -eq 'APPROVED'} | Measure-Object).Count
$declined = ($allActions | Where-Object {$_.status -eq 'DECLINED'} | Measure-Object).Count
$executed = ($allActions | Where-Object {$_.status -eq 'EXECUTED'} | Measure-Object).Count
$failed = ($allActions | Where-Object {$_.status -eq 'FAILED'} | Measure-Object).Count

Write-Host "PENDING       : $pending"
Write-Host "APPROVED      : $approved"
Write-Host "DECLINED      : $declined"
Write-Host "EXECUTED      : $executed"
Write-Host "FAILED        : $failed"

Write-Host "`n[2] APPROVAL RATE (Quality Metric)" -ForegroundColor Yellow
Write-Host ("-"*60) -ForegroundColor Gray

$total_decided = $approved + $declined
if ($total_decided -gt 0) {
    $approval_rate = $approved / $total_decided
    Write-Host "Approved      : $approved items"
    Write-Host "Declined      : $declined items"
    Write-Host "Approval Rate : $([math]::Round($approval_rate * 100, 1))%"
} else {
    Write-Host "No decisions made yet (all items pending)"
}

Write-Host "`n[3] SANDBOX EVENT TYPES" -ForegroundColor Yellow
Write-Host ("-"*60) -ForegroundColor Gray

$response = Invoke-WebRequest -Uri "$base_url/api/sandbox/activity?limit=1000" -Method GET -Headers $headers -UseBasicParsing
$allEvents = $response.Content | ConvertFrom-Json

$eventTypes = $allEvents | Group-Object -Property event_type | Select-Object Name, Count | Sort-Object Count -Descending
foreach ($type in $eventTypes) {
    Write-Host "$($type.Name.PadRight(35)) : $($type.Count)"
}

Write-Host "`n[4] HUMAN LABELS (Learning Signal)" -ForegroundColor Yellow
Write-Host ("-"*60) -ForegroundColor Gray

# Get all events and filter to labels
$labelEvents = $allEvents | Where-Object {$_.event_type -eq 'HUMAN_LABEL_CREATED'}
$approveCount = 0
$rejectCount = 0
$needsInfoCount = 0

foreach ($event in $labelEvents) {
    if ($event.payload) {
        $label = $event.payload.label
        if ($label -eq 'APPROVE') { $approveCount++ }
        elseif ($label -eq 'REJECT') { $rejectCount++ }
        elseif ($label -eq 'NEEDS_INFO') { $needsInfoCount++ }
    }
}

$totalLabels = $approveCount + $rejectCount + $needsInfoCount
if ($totalLabels -gt 0) {
    Write-Host "APPROVE       : $approveCount ($([math]::Round($approveCount/$totalLabels*100,1))%)"
    Write-Host "REJECT        : $rejectCount ($([math]::Round($rejectCount/$totalLabels*100,1))%)"
    Write-Host "NEEDS_INFO    : $needsInfoCount ($([math]::Round($needsInfoCount/$totalLabels*100,1))%)"
} else {
    Write-Host "No labels created yet"
}

Write-Host "`n" + ("="*60) -ForegroundColor Green
Write-Host "INTERPRETATION" -ForegroundColor Green
Write-Host ("="*60) -ForegroundColor Green

Write-Host "`nSafety (False Positive Rate):" -ForegroundColor Yellow
if ($declined -eq 0) {
    Write-Host "  FP Rate = 0% (No declined items = no false positives detected)" -ForegroundColor Green
} else {
    $fp_rate = $declined / ($approved + $declined)
    Write-Host "  FP Rate = $([math]::Round($fp_rate*100,1))% (Lower is better)" -ForegroundColor Gray
}

Write-Host "`nSignal Quality:" -ForegroundColor Yellow
if ($approval_rate -gt 0.7) {
    Write-Host "  Approval rate $([math]::Round($approval_rate*100,1))% indicates good item quality" -ForegroundColor Green
} elseif ($approval_rate -gt 0.5) {
    Write-Host "  Approval rate $([math]::Round($approval_rate*100,1))% - moderate quality" -ForegroundColor Yellow
} else {
    Write-Host "  Approval rate $([math]::Round($approval_rate*100,1))% - items need tuning" -ForegroundColor Red
}

Write-Host "`nLearning Progress:" -ForegroundColor Yellow
if ($totalLabels -ge 20) {
    Write-Host "  Strong signal: $totalLabels labels collected (good for training)" -ForegroundColor Green
} elseif ($totalLabels -ge 5) {
    Write-Host "  Emerging signal: $totalLabels labels (label more items to improve)" -ForegroundColor Yellow
} else {
    Write-Host "  Limited signal: Only $totalLabels labels (need 20+ for effective learning)" -ForegroundColor Red
}

Write-Host "`n" + ("="*60) -ForegroundColor Cyan
