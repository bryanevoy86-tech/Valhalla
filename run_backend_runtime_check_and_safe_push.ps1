# =========================
# VALHALLA RUNTIME CHECK + SAFE PUSH
# =========================

param(
    [string]$BranchName = "pre-weweb-stable",
    [int]$Port = 4000,
    [int]$TimeoutSeconds = 25,
    [switch]$SkipPush = $false
)

$ErrorActionPreference = "Stop"

# Function to check if port is available
function Test-PortAvailable {
    param([int]$Port)
    $sock = New-Object System.Net.Sockets.TcpClient
    try {
        $sock.Connect("127.0.0.1", $Port)
        $sock.Close()
        return $false  # Port is in use
    }
    catch {
        return $true  # Port is available
    }
}

# Find available port if needed
if (-not (Test-PortAvailable $Port)) {
    Write-Host "Port $Port is in use, finding alternative..." -ForegroundColor Yellow
    $originalPort = $Port
    for ($i = $Port + 1; $i -lt $Port + 100; $i++) {
        if (Test-PortAvailable $i) {
            $Port = $i
            Write-Host "Using port $Port instead" -ForegroundColor Yellow
            break
        }
    }
    if ($Port -eq $originalPort) {
        throw "Could not find available port"
    }
}

function Write-Section($text) {
    Write-Host ""
    Write-Host "=== $text ===" -ForegroundColor Cyan
}

function Test-CommandExists($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Invoke-TimedRequest {
    param(
        [string]$Url,
        [int]$TimeoutSec = 15
    )

    $result = [ordered]@{
        url = $Url
        ok = $false
        status = $null
        elapsed_ms = $null
        error = $null
        body_preview = $null
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -UseBasicParsing
        $sw.Stop()
        $result.ok = $true
        $result.status = [int]$response.StatusCode
        $result.elapsed_ms = [int]$sw.ElapsedMilliseconds
        $content = $response.Content
        if ($content.Length -gt 500) {
            $content = $content.Substring(0, 500)
        }
        $result.body_preview = $content
    }
    catch {
        $sw.Stop()
        $result.elapsed_ms = [int]$sw.ElapsedMilliseconds
        $result.error = $_.Exception.Message
    }

    return [pscustomobject]$result
}

function Save-Json($path, $data) {
    $dir = Split-Path $path -Parent
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
    $data | ConvertTo-Json -Depth 8 | Set-Content -Path $path -Encoding UTF8
}

Write-Section "Preflight"

if (!(Test-CommandExists "python")) {
    throw "python not found in PATH"
}
if (!(Test-CommandExists "git")) {
    throw "git not found in PATH"
}

$repoRoot = Get-Location
Write-Host "Repo root: $repoRoot"

$resultsDir = Join-Path $repoRoot "DRYRUN_RESULTS"
if (!(Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir | Out-Null
}

$stdoutLog = Join-Path $resultsDir "runtime_uvicorn_stdout.log"
$stderrLog = Join-Path $resultsDir "runtime_uvicorn_stderr.log"
$runtimeJson = Join-Path $resultsDir "runtime_probe_results.json"
$summaryTxt = Join-Path $resultsDir "runtime_probe_summary.txt"

if (Test-Path $stdoutLog) { Remove-Item $stdoutLog -Force }
if (Test-Path $stderrLog) { Remove-Item $stderrLog -Force }

Write-Section "Start backend"

# Set required environment variables for backend
$env:DATABASE_URL = "sqlite:///valhalla_test.db"
$env:VALHALLA_JWT_SECRET = "dev-test-secret-key-12345"
$env:BACKEND_PORT = $Port

$pythonExe = (Get-Command python).Source

# Use the start_backend.py wrapper that handles module registration
$startBackendScript = Join-Path $repoRoot "start_backend.py"
if (!(Test-Path $startBackendScript)) {
    # Fallback: use direct uvicorn with env setup
    $uvicornArgs = "-m uvicorn app.main:app --host 127.0.0.1 --port $Port --log-level info"
    $proc = Start-Process `
        -FilePath $pythonExe `
        -ArgumentList $uvicornArgs `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru `
        -NoNewWindow
}
else {
    # Use starter script with port parameter
    $proc = Start-Process `
        -FilePath $pythonExe `
        -ArgumentList "$startBackendScript $Port" `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -PassThru `
        -NoNewWindow
}

Write-Host "Started uvicorn PID: $($proc.Id)"
Write-Host "Waiting for backend to become ready..."

$maxWaitSeconds = 30
$pollIntervalMs = 500
$startTime = Get-Date
$ready = $false

while (((Get-Date) - $startTime).TotalSeconds -lt $maxWaitSeconds) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $ready = $true
            Write-Host "Backend is ready!" -ForegroundColor Green
            break
        }
    }
    catch {
        # Not ready yet, continue waiting
    }
    
    Start-Sleep -Milliseconds $pollIntervalMs
}

if (-not $ready) {
    Write-Host "Backend did not respond to /health within $maxWaitSeconds seconds" -ForegroundColor Red
}

if ($proc.HasExited) {
    Write-Host "Backend exited. Check logs:" -ForegroundColor Red
    Write-Host "STDOUT: $stdoutLog"
    Write-Host "STDERR: $stderrLog"
    Get-Content $stdoutLog -ErrorAction SilentlyContinue | Select-Object -Last 20 | Write-Host
    Get-Content $stderrLog -ErrorAction SilentlyContinue | Select-Object -Last 20 | Write-Host
    throw "Backend failed to stay running"
}

Write-Section "Probe endpoints"

$base = "http://127.0.0.1:$Port"
$endpoints = @(
    "$base/health",
    "$base/api/compliance/mode",
    "$base/api/legal/templates",
    "$base/api/finance/status/summary"
)

$probeResults = @()
foreach ($ep in $endpoints) {
    Write-Host "Testing $ep ..."
    $probeResults += Invoke-TimedRequest -Url $ep -TimeoutSec $TimeoutSeconds
}

Save-Json -path $runtimeJson -data $probeResults

$allOk = $true
$slowCount = 0

$lines = @()
$lines += "VALHALLA RUNTIME PROBE SUMMARY"
$lines += "Generated: $(Get-Date -Format o)"
$lines += ""

foreach ($r in $probeResults) {
    $line = "{0} | ok={1} | status={2} | elapsed_ms={3} | error={4}" -f `
        $r.url, $r.ok, $r.status, $r.elapsed_ms, $r.error
    $lines += $line

    if (-not $r.ok) {
        $allOk = $false
    }
    if ($r.elapsed_ms -gt 4000) {
        $slowCount += 1
    }
}

$lines | Set-Content -Path $summaryTxt -Encoding UTF8
Get-Content $summaryTxt

Write-Section "Interpretation"

$health = $probeResults | Where-Object { $_.url -like "*/health" } | Select-Object -First 1
$compliance = $probeResults | Where-Object { $_.url -like "*/api/compliance/mode" } | Select-Object -First 1
$legal = $probeResults | Where-Object { $_.url -like "*/api/legal/templates" } | Select-Object -First 1
$finance = $probeResults | Where-Object { $_.url -like "*/api/finance/status/summary" } | Select-Object -First 1

$diagnosis = "unknown"

if ($allOk -and $slowCount -eq 0) {
    $diagnosis = "healthy"
}
elseif ($health.ok -and $health.elapsed_ms -lt 1500 -and (($legal.elapsed_ms -gt 4000) -or ($finance.elapsed_ms -gt 4000) -or ($compliance.elapsed_ms -gt 4000))) {
    $diagnosis = "heavy_route_issue"
}
elseif ($allOk -eq $false) {
    $diagnosis = "runtime_failure"
}
else {
    $diagnosis = "slow_start_or_general_latency"
}

Write-Host "Diagnosis: $diagnosis" -ForegroundColor Yellow

Write-Section "Stop backend"
try {
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
        Start-Sleep -Seconds 1
    }
}
catch {
    Write-Host "Could not stop backend cleanly: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Section "Decision"

# Safe-to-push rules:
# - all probes pass
# - /health under 2000ms
# - no more than 1 slow endpoint > 4000ms
# - diagnosis not runtime_failure
$safeToPush = $allOk -and ($health.elapsed_ms -lt 2000) -and ($slowCount -le 1) -and ($diagnosis -ne "runtime_failure")

if (-not $safeToPush) {
    Write-Host "SAFE PUSH BLOCKED" -ForegroundColor Red
    Write-Host "Review these files:"
    Write-Host "  $summaryTxt"
    Write-Host "  $runtimeJson"
    Write-Host "  $stdoutLog"
    Write-Host "  $stderrLog"
    exit 2
}

Write-Host "Runtime checks passed. Safe push allowed." -ForegroundColor Green

Write-Section "Git status"
git status --short

Write-Section "Create checkpoint commit"
try {
    git rev-parse --verify $BranchName 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        git checkout -b $BranchName
    }
    else {
        git checkout $BranchName
    }
}
catch {
    git checkout -b $BranchName
}

git add .
git commit -m "BACKEND VERIFIED: runtime probes passed + legal finance compliance stable" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "No new commit created (possibly no file changes)." -ForegroundColor Yellow
}
else {
    Write-Host "Checkpoint commit created." -ForegroundColor Green
}

if ($SkipPush) {
    Write-Section "Push skipped by flag"
    exit 0
}

Write-Section "Push branch"
git push origin $BranchName

Write-Section "Done"
Write-Host "Branch pushed: $BranchName" -ForegroundColor Green
Write-Host "Artifacts saved in: $resultsDir"
