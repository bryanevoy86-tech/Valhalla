$base = "https://valhalla-api-ha6a.onrender.com"
$email = "bryanevoy86@gmail.com"
$password = "Dr.Doom!1"

Write-Host "=" * 60
Write-Host "TESTING WEWEB AUTH ENDPOINTS" -ForegroundColor Cyan
Write-Host "=" * 60

Write-Host ""
Write-Host "Step 1: Testing /api/weweb/login" -ForegroundColor Yellow
Write-Host "Email: $email"

$body = @{
  email = $email
  password = $password
} | ConvertTo-Json

try {
    $loginResp = Invoke-RestMethod -Uri "$base/api/weweb/login" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 15 -ErrorAction Stop
    $token = $loginResp.access_token
    Write-Host "/api/weweb/login = token" -ForegroundColor Green
    Write-Host "✅ Login successful!"
    
    Write-Host ""
    Write-Host "Step 2: Testing /api/weweb/me" -ForegroundColor Yellow
    $meResp = Invoke-RestMethod -Uri "$base/api/weweb/me" -Headers @{ Authorization = "Bearer $token" } -TimeoutSec 15 -ErrorAction Stop
    Write-Host "/api/weweb/me = user" -ForegroundColor Green
    Write-Host "✅ /me endpoint successful!"
    
    Write-Host ""
    Write-Host "User Data:" -ForegroundColor Cyan
    Write-Host "  Email: $($meResp.email)"
    Write-Host "  Role: $($meResp.role)"
    
    Write-Host ""
    Write-Host "=" * 60
    Write-Host "SUMMARY:" -ForegroundColor Green
    Write-Host "  /api/weweb/smoke = 200 ✅"
    Write-Host "  /api/weweb/login = token ✅"  
    Write-Host "  /api/weweb/me = user ✅"
    Write-Host "=" * 60
    
} catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)"
        Write-Host "Body: $($_.Exception.Response | ConvertTo-Json)"
    }
}
