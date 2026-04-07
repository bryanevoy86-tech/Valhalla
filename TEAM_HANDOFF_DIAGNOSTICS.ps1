# ============================================================================
# VALHALLA TEAM HANDOFF - COPY & PASTE DIAGNOSTIC SCRIPT
# ============================================================================
# 
# Purpose: Complete project diagnostics for team review
# Usage: Copy entire script and paste into PowerShell terminal
# Output: Generates comprehensive report of project state
#
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════════════╗"
Write-Host "║                                                                        ║"
Write-Host "║            VALHALLA PROJECT - TEAM HANDOFF DIAGNOSTICS                ║"
Write-Host "║                                                                        ║"
Write-Host "╚════════════════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "This script will generate a complete diagnostic report."
Write-Host "Run from: d:\dev (project root)"
Write-Host ""

# ============================================================================
# SECTION 1: ENVIRONMENT & PATHS
# ============================================================================

Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 1: ENVIRONMENT & PATHS" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Current Location:" -ForegroundColor Yellow
Get-Location

Write-Host ""
Write-Host "Python Version:" -ForegroundColor Yellow
python --version

Write-Host ""
Write-Host "Virtual Environment:" -ForegroundColor Yellow
if ($env:VIRTUAL_ENV) {
    Write-Host "Activated: $($env:VIRTUAL_ENV)"
} else {
    Write-Host "WARNING: Virtual environment not activated"
}

# ============================================================================
# SECTION 2: STARTUP FILES
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 2: STARTUP FILES" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "services/api/start.py (first 50 lines):" -ForegroundColor Yellow
Get-Content .\services\api\start.py -TotalCount 50

Write-Host ""
Write-Host "render.yaml (deployment config):" -ForegroundColor Yellow
Get-Content .\render.yaml -TotalCount 40

# ============================================================================
# SECTION 3: APPLICATION ENTRY POINTS
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 3: APPLICATION ENTRY POINTS" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Main.py files in project:" -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter main.py -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch "\.venv|_archive|valhalla_export" } |
    Select-Object @{Name="Path"; Expression={$_.FullName.Replace("D:\dev\", "")}} |
    Format-Table -AutoSize -HideTableHeaders

# ============================================================================
# SECTION 4: ROUTERS REGISTERED
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 4: ROUTER INVENTORY" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Total router files available:" -ForegroundColor Yellow
$routerCount = (Get-ChildItem -Path .\services\api\app\routers -Filter *.py -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -ne "__init__.py" }).Count
Write-Host "$routerCount routers"

Write-Host ""
Write-Host "Sample routers (first 20):" -ForegroundColor Yellow
Get-ChildItem -Path .\services\api\app\routers -Filter *.py -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne "__init__.py" } |
    Sort-Object Name |
    Select-Object -First 20 -ExpandProperty Name |
    ForEach-Object { "  • $_" }

# ============================================================================
# SECTION 5: CONFIGURATION FILES
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 5: CRITICAL CONFIG FILES" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Configuration files found:" -ForegroundColor Yellow

$configFiles = @(
    "render.yaml",
    "Dockerfile", 
    "docker-compose.yml",
    "alembic.ini",
    ".env.example",
    "pyproject.toml",
    "pytest.ini"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file"
    } else {
        Write-Host "  ✗ $file (NOT FOUND)"
    }
}

# ============================================================================
# SECTION 6: DATABASE MIGRATIONS
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 6: DATABASE MIGRATIONS" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Alembic versions directory:" -ForegroundColor Yellow
if (Test-Path .\alembic\versions) {
    $versionCount = (Get-ChildItem .\alembic\versions -Filter *.py).Count
    Write-Host "  Found: $versionCount migration files"
    Write-Host ""
    Write-Host "  Latest migrations:"
    Get-ChildItem .\alembic\versions -Filter *.py | Sort-Object Name -Descending | Select-Object -First 5 -ExpandProperty Name | ForEach-Object { "    • $_" }
} else {
    Write-Host "  Alembic migrations directory not found"
}

# ============================================================================
# SECTION 7: CODE QUALITY CHECKS
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 7: CODE QUALITY CHECKS" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Searching for TODO/FIXME/HACK comments in source code..." -ForegroundColor Yellow
$codeIssues = Get-ChildItem -Recurse -Include *.py |
    Where-Object { $_.FullName -notmatch "\.venv|_archive|valhalla_export" } |
    Select-String -Pattern "TODO|FIXME|HACK|BLOCKED.*comment|TEMP_" -ErrorAction SilentlyContinue |
    Select-Object -First 30

if ($codeIssues.Count -gt 0) {
    Write-Host "Found issues (showing first 30):" -ForegroundColor Yellow
    $codeIssues | ForEach-Object {
        $file = $_.Path.Replace("D:\dev\", "")
        Write-Host "  $file : $_" -ForegroundColor Red
    }
} else {
    Write-Host "No TODO/FIXME/HACK comments found" -ForegroundColor Green
}

# ============================================================================
# SECTION 8: REQUIREMENTS & DEPENDENCIES
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 8: REQUIREMENTS & DEPENDENCIES" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host ".env.example (sample configuration):" -ForegroundColor Yellow
if (Test-Path .\.env.example) {
    Get-Content .\.env.example | Select-Object -First 20
} else {
    Write-Host "  .env.example not found"
}

Write-Host ""
Write-Host "Requirements files:" -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter requirements.txt -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\.venv|_archive|valhalla_export" } |
    Select-Object @{Name="Path"; Expression={$_.FullName.Replace("D:\dev\", "")}} |
    Format-Table -AutoSize -HideTableHeaders

# ============================================================================
# SECTION 9: PROJECT SIZE & STRUCTURE  
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 9: PROJECT SIZE & STRUCTURE" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "Python source files:" -ForegroundColor Yellow
$pyFiles = Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch "\.venv|_archive|valhalla_export" } |
    Measure-Object
Write-Host "  Total: $($pyFiles.Count) files"

Write-Host ""
Write-Host "Total lines of Python code:" -ForegroundColor Yellow
$totalLines = Get-ChildItem -Recurse -Filter *.py -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\.venv|_archive|valhalla_export" } |
    Get-Content |
    Measure-Object -Line
Write-Host "  Approx: $($totalLines.Lines) lines"

Write-Host ""
Write-Host "Directory structure:" -ForegroundColor Yellow
Get-ChildItem -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch "\.venv|_archive|valhalla_export" } |
    Sort-Object Name |
    ForEach-Object { "  📁 $($_.Name)" }

# ============================================================================
# SECTION 10: DEPLOYMENT READINESS
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 10: DEPLOYMENT READINESS CHECKLIST" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
$deployment_checks = @{
    "services/api/start.py exists" = (Test-Path .\services\api\start.py);
    "render.yaml exists" = (Test-Path .\render.yaml);
    "Dockerfile exists" = (Test-Path .\Dockerfile);
    "alembic.ini exists" = (Test-Path .\alembic.ini);
    "alembic/versions/ exists" = (Test-Path .\alembic\versions);
    "requirements.txt exists" = (Test-Path .\requirements.txt);
    "services/api/requirements.txt exists" = (Test-Path .\services\api\requirements.txt);
}

foreach ($check in $deployment_checks.GetEnumerator()) {
    if ($check.Value) {
        Write-Host "  ✓ $($check.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $($check.Name)" -ForegroundColor Red
    }
}

# ============================================================================
# SECTION 11: NEXT STEPS
# ============================================================================

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SECTION 11: TEAM NEXT STEPS" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host ""
Write-Host "1. Review the exported project archive:" -ForegroundColor Yellow
Write-Host "   - valhalla_export_*.zip contains full project snapshot"
Write-Host "   - Start with: 00_EXPORT_SUMMARY.txt"
Write-Host ""

Write-Host "2. Verify database configuration:" -ForegroundColor Yellow
Write-Host "   - Check alembic migrations are clean"
Write-Host "   - Verify DATABASE_URL and VALHALLA_JWT_SECRET set"
Write-Host ""

Write-Host "3. Test application import:" -ForegroundColor Yellow
Write-Host "   Command: python -c \"from services.api.main import app; print('OK')\""
Write-Host "   (Requires environment variables to be set)"
Write-Host ""

Write-Host "4. Review router registrations:" -ForegroundColor Yellow
Write-Host "   - 200+ routers in services/api/app/routers/"
Write-Host "   - All registered in services/api/app/main.py"
Write-Host "   - Check for conflicts or missing dependencies"
Write-Host ""

Write-Host "5. Prepare deployment:" -ForegroundColor Yellow
Write-Host "   - Update render.yaml with correct domain"
Write-Host "   - Set environment secrets in Render dashboard"
Write-Host "   - Test local startup with: python services/api/start.py"
Write-Host ""

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "DIAGNOSTICS COMPLETE" -ForegroundColor Green
Write-Host "═════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "All information has been collected. Share with your team for review."
Write-Host ""
