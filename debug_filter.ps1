# Debug: Check what metrics are actually in the payload
$base_url = "https://valhalla-api-ha6a.onrender.com"
$key = "a774e90bcc3de95f0513782e41fc454f"
$headers = @{ "X-API-Key" = $key; "Content-Type" = "application/json" }

Write-Host "Testing with rich payload metrics..." -ForegroundColor Cyan

$body = @{
    url = "https://webhook.example.com/debug"
    payload = @{
        expected_profit = 5000  # Below threshold
        roi_percentage = 5      # Below threshold
        risk_score = 30         # Above threshold
        deal_id = "debug-001"
    }
} | ConvertTo-Json -Depth 10

Write-Host "Sending payload: " -ForegroundColor Gray
Write-Host $body -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$base_url/api/notify/webhook" -Method POST -Headers $headers -Body $body -TimeoutSec 10
    Write-Host "`nResponse:" -ForegroundColor Cyan
    Write-Host ($response | ConvertTo-Json -Depth 10) -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

# Check the activity log to see what events were created
Write-Host "`n`nChecking activity log..." -ForegroundColor Cyan
try {
    $activity = Invoke-RestMethod -Uri "$base_url/api/sandbox/activity?limit=5" -Method GET -Headers $headers -TimeoutSec 10
    Write-Host "Recent events:" -ForegroundColor Gray
    foreach ($event in $activity) {
        Write-Host "  $($event.event_type) at $($event.created_at)" -ForegroundColor Gray
    }
} catch {
    Write-Host "Error fetching activity: $_" -ForegroundColor Red
}
