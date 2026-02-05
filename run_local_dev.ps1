$ErrorActionPreference = "Stop"

$root = "C:\dev\valhalla"
$api  = "$root\services\api"
$logs = "$root\logs"

New-Item -ItemType Directory -Force -Path $logs | Out-Null

# Kill prior uvicorns (optional)
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -like "*uvicorn*app.main:app*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

cd $api

$env:PYTHONPATH = $api
$env:DATABASE_URL = "sqlite:///dev.db"
$env:VALHALLA_JWT_SECRET = "dev-secret"
$env:VALHALLA_API_KEY = "dev-key"

Start-Process -FilePath python `
  -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8010","--log-level","info") `
  -WindowStyle Normal `
  -RedirectStandardOutput "$logs\uvicorn.out.log" `
  -RedirectStandardError  "$logs\uvicorn.err.log"

Write-Host "Valhalla started on http://127.0.0.1:8010"
Write-Host "Logs: $logs\uvicorn.out.log / $logs\uvicorn.err.log"
