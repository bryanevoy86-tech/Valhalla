# VALHALLA TEAM HANDOFF - SIMPLIFIED DIAGNOSTICS SCRIPT
# Copy & paste this into PowerShell at d:\dev

Write-Host "Starting Valhalla Diagnostics..." -ForegroundColor Cyan
Write-Host ""

# 1. Environment
Write-Host "=== ENVIRONMENT ===" -ForegroundColor Yellow
Write-Host "Location: $(Get-Location)"
Write-Host "Python: $(python --version 2>&1)"
Write-Host ""

# 2. Critical Files
Write-Host "=== CRITICAL FILES ===" -ForegroundColor Yellow
$files = @("services/api/start.py", "render.yaml", "Dockerfile", "alembic.ini")
foreach ($f in $files) {
    if (Test-Path $f) { Write-Host "[OK] $f" } else { Write-Host "[MISSING] $f" }
}
Write-Host ""

# 3. Routers Count
Write-Host "=== ROUTERS ===" -ForegroundColor Yellow
$count = (Get-ChildItem .\services\api\app\routers -Filter *.py | Where-Object {$_.Name -ne "__init__.py"}).Count
Write-Host "Total routers registered: $count"
Write-Host ""

# 4. Code Files
Write-Host "=== CODE SIZE ===" -ForegroundColor Yellow
$py = (Get-ChildItem -Recurse -Filter *.py | Where-Object {$_.FullName -notmatch "\.venv|_archive"}).Count
$lines = (Get-ChildItem -Recurse -Filter *.py | Where-Object {$_.FullName -notmatch "\.venv|_archive"} | Get-Content | Measure-Object -Line).Lines
Write-Host "Python files: $py"
Write-Host "Total lines: $lines"
Write-Host ""

# 5. Database Migrations
Write-Host "=== ALEMBIC MIGRATIONS ===" -ForegroundColor Yellow
if (Test-Path .\alembic\versions) {
    $migrations = (Get-ChildItem .\alembic\versions -Filter *.py).Count
    Write-Host "Migration files: $migrations"
}
Write-Host ""

# 6. Main Entry Points
Write-Host "=== ENTRY POINTS ===" -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter main.py | Where-Object {$_.FullName -notmatch "\.venv|_archive|valhalla_export"} | ForEach-Object {
    $path = $_.FullName.Replace("D:\dev\", "")
    Write-Host "  - $path"
}
Write-Host ""

Write-Host "Diagnostics complete. Check DIAGNOSTIC_REPORT.txt for full details."
