
# =========================
# VALHALLA FULL EXPORT SCRIPT (PowerShell)
# =========================
# This script exports the entire Valhalla project structure and code
# for team review and audit purposes.

param(
    [string]$OutputFolder = "valhalla_export",
    [switch]$NoZip = $false
)

Write-Host "========================================"
Write-Host "Starting Valhalla Full System Export..."
Write-Host "========================================"
Write-Host ""

# Create export folder
if (Test-Path $OutputFolder) {
    Remove-Item $OutputFolder -Recurse -Force
    Write-Host "Cleaned existing export folder"
}
New-Item -ItemType Directory -Path $OutputFolder -Force | Out-Null
Write-Host "[OK] Export folder created: $OutputFolder"
Write-Host ""

# ==================== 1. PROJECT STRUCTURE ====================
Write-Host "1. Capturing project structure..." -ForegroundColor Yellow
$structureFile = Join-Path $OutputFolder "00_PROJECT_STRUCTURE.txt"
@"
=== VALHALLA PROJECT STRUCTURE ===
Generated: $(Get-Date)
Machine: $($env:COMPUTERNAME)
User: $($env:USERNAME)

Directory tree (max depth: 3, excluding .venv, __pycache__, .git, node_modules):

"@ | Out-File $structureFile

try {
    $excludeDirs = @(".venv", "venv", "env", "__pycache__", ".git", ".github", "node_modules", "build", "dist", ".pytest_cache", ".mypy_cache", "_archive", "_temp_guard_test.py")
    
    function Get-DirectoryTree {
        param(
            [string]$Path,
            [int]$Depth = 0,
            [int]$MaxDepth = 3
        )
        
        if ($Depth -gt $MaxDepth) { return }
        
        $indent = "  " * $Depth
        
        try {
            $items = Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { $_.Name -notin $excludeDirs }
            
            foreach ($item in $items | Sort-Object -Property Name) {
                if ($item.PSIsContainer) {
                    Add-Content $structureFile "$indent|-- $($item.Name)/"
                    Get-DirectoryTree -Path $item.FullName -Depth ($Depth + 1) -MaxDepth $MaxDepth
                } else {
                    $sizeKB = [math]::Round($item.Length / 1KB, 1)
                    Add-Content $structureFile "$indent|-- $($item.Name) ($sizeKB KB)"
                }
            }
        } catch {}
    }
    
    Get-DirectoryTree -Path (Get-Location).Path
    Write-Host "[OK] Project structure saved"
} catch {
    Write-Host "[WARN] Could not generate full tree structure" -ForegroundColor Yellow
}
Write-Host ""

# ==================== 2. ENVIRONMENT & DEPENDENCIES ====================
Write-Host "2. Capturing environment info..." -ForegroundColor Yellow

try {
    pip freeze | Out-File (Join-Path $OutputFolder "01_REQUIREMENTS_FROZEN.txt")
    Write-Host "[OK] Current pip packages frozen"
} catch {
    Write-Host "[WARN] Could not freeze pip packages" -ForegroundColor Yellow
}

# Copy actual requirements files
foreach ($reqFile in @("requirements.txt", "services/api/requirements.txt")) {
    if (Test-Path $reqFile) {
        Copy-Item $reqFile (Join-Path $OutputFolder "01_$(Split-Path $reqFile -Leaf)")
    }
}
Write-Host "[OK] Requirements files copied"
Write-Host ""

# ==================== 3. DATABASE MIGRATIONS ====================
Write-Host "3. Capturing database migration state..." -ForegroundColor Yellow

try {
    $migrationFile = Join-Path $OutputFolder "02_ALEMBIC_STATE.txt"
    @"
=== ALEMBIC MIGRATION STATE ===
Generated: $(Get-Date)

--- CURRENT REVISION ---
"@ | Out-File $migrationFile

    alembic current 2>&1 | Add-Content $migrationFile
    
    @"

--- MIGRATION HISTORY ---
"@ | Add-Content $migrationFile
    
    alembic history 2>&1 | Add-Content $migrationFile
    Write-Host "[OK] Alembic migration state saved"
} catch {
    Write-Host "[WARN] Alembic not available or migrations not initialized" -ForegroundColor Yellow
}
Write-Host ""

# ==================== 4. CRITICAL CONFIG FILES ====================
Write-Host "4. Copying critical configuration files..." -ForegroundColor Yellow

$criticalFiles = @(
    "render.yaml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".dockerignore",
    "start.py",
    "alembic.ini",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    ".env.example",
    "pytest.ini"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Copy-Item $file (Join-Path $OutputFolder "03_CONFIG_$(Split-Path $file -Leaf)") -ErrorAction SilentlyContinue
        Write-Host "  [OK] $file"
    }
}
Write-Host ""

# ==================== 5. ALEMBIC MIGRATIONS ====================
Write-Host "5. Copying database migrations..." -ForegroundColor Yellow

if (Test-Path "alembic") {
    Copy-Item -Path "alembic" -Destination (Join-Path $OutputFolder "04_ALEMBIC") -Recurse -ErrorAction SilentlyContinue
    Write-Host "[OK] Alembic migrations copied"
}
Write-Host ""

# ==================== 6. APPLICATION CODE ====================
Write-Host "6. Copying application code..." -ForegroundColor Yellow

$appDirs = @("services", "app", "backend")

foreach ($dir in $appDirs) {
    if (Test-Path $dir) {
        Copy-Item -Path $dir -Destination (Join-Path $OutputFolder "05_CODE_$dir") -Recurse -ErrorAction SilentlyContinue
        Write-Host "  [OK] $dir/ copied"
    }
}
Write-Host ""

# ==================== 7. DOCUMENTATION ====================
Write-Host "7. Copying documentation..." -ForegroundColor Yellow

$docFiles = Get-ChildItem -Path . -Filter "*.md" -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch "^(README|CHANGELOG)" }

if ($docFiles.Count -gt 0) {
    $docsFolder = Join-Path $OutputFolder "06_DOCS"
    New-Item -ItemType Directory -Path $docsFolder -Force | Out-Null
    
    foreach ($doc in $docFiles) {
        Copy-Item $doc.FullName $docsFolder -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] $($docFiles.Count) documentation files copied"
}
Write-Host ""

# ==================== 8. CLEANUP ====================
Write-Host "8. Cleaning unnecessary files..." -ForegroundColor Yellow

$cleanupPatterns = @("__pycache__", ".pytest_cache", ".mypy_cache", "*.pyc", ".DS_Store", "*.egg-info")

foreach ($pattern in $cleanupPatterns) {
    Get-ChildItem -Path $OutputFolder -Recurse -Filter $pattern -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "[OK] Cleanup complete"
Write-Host ""

# ==================== 9. SUMMARY REPORT ====================
Write-Host "9. Generating summary report..." -ForegroundColor Yellow

$summaryFile = Join-Path $OutputFolder "00_EXPORT_SUMMARY.txt"
$exportSize = (Get-ChildItem $OutputFolder -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

@"
================================================================================
                 VALHALLA PROJECT EXPORT SUMMARY REPORT
================================================================================

EXPORT DETAILS
==============
Export Date:        $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Export Location:    $(Join-Path (Get-Location) $OutputFolder)
Export Size:        $([math]::Round($exportSize, 2)) MB

CONTENTS INCLUDED
=================
[OK] Project structure and file listing
[OK] Environment and dependencies (pip requirements)
[OK] Database migration history (Alembic state)
[OK] Critical configuration files (Docker, render.yaml, etc.)
[OK] Alembic migration scripts
[OK] Full application code (services, app, backend)
[OK] Project documentation (*.md files)

EXCLUDED ITEMS (for cleanliness)
================================
[X] Virtual environments (.venv, venv, env)
[X] Python cache (__pycache__, .pytest_cache, .mypy_cache)
[X] Git metadata (.git, .github)
[X] Node modules (if any)
[X] Build artifacts (build/, dist/)
[X] Archive folders (_archive)

WHAT YOUR TEAM SHOULD REVIEW
=============================

1. 00_EXPORT_SUMMARY.txt
   -> This file - quick reference

2. 03_CONFIG_* files
   -> Deployment config (render.yaml, Dockerfile)
   -> Application startup (start.py)
   -> Database config (alembic.ini)

3. 05_CODE_services/
   -> Main application code (FastAPI services)
   -> Routes, routers, models, schemas
   -> Middleware, core utilities

4. 05_CODE_app/
   -> Likely duplicate or specialized modules

5. 04_ALEMBIC/
   -> Database migration scripts
   -> Check versions/ folder for all applied migrations

6. 01_REQUIREMENTS_*.txt
   -> All Python dependencies
   -> Check for security updates or conflicts

7. 06_DOCS/
   -> Architecture docs, deployment guides, etc.

KEY CHECKS FOR TEAM
===================

[] All critical routers are registered in main.py/services/api/app/main.py
   -> Look for include_router() calls - ensure no routers are missing

[] Database migrations are applied
   -> Run: alembic current (should show latest revision)
   -> Run: alembic history (should show clean migration chain)

[] Required dependencies are in requirements.txt
   -> Compare with 01_REQUIREMENTS_FROZEN.txt
   -> Check for any security vulnerabilities

[] Environment variables are documented
   -> Look for .env.example
   -> Verify all required vars are set in deployment (render.yaml)

[] No incomplete features
   -> Search for TODO, FIXME, HACK comments
   -> Check for commented-out code blocks

[] API endpoints are documented
   -> Review routers for endpoint definitions
   -> Verify paths, methods, and authentication requirements

DEPLOYMENT NOTES
================

Entry Point:        services/api/main.py:app
Command:            uvicorn services.api.main:app --host 0.0.0.0 --port 8000
Or via Docker:      See Dockerfile for container image
Or via Render:      See render.yaml for deployment config

QUICK START FOR TEAM
====================

1. Unzip this export
2. Review files in order (00_EXPORT_SUMMARY -> 03_CONFIG -> 05_CODE)
3. Search codebase for incomplete patterns:
   - grep -r "TODO" 05_CODE_*
   - grep -r "FIXME" 05_CODE_*
   - grep -r "import.*but never used" 05_CODE_*
4. Verify database migrations are clean
5. Check all dependencies are explicitly listed in requirements.txt

================================================================================
Generated by: Valhalla Export Script v1.0
Generated on: $(Get-Date)
"@ | Out-File $summaryFile

Write-Host "[OK] Summary report generated"
Write-Host ""

# ==================== 10. CREATE ZIP ====================
if (-not $NoZip) {
    Write-Host "10. Creating compressed archive..." -ForegroundColor Yellow
    
    try {
        $zipPath = "valhalla_export_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip"
        
        # Use PowerShell compression
        Compress-Archive -Path $OutputFolder -DestinationPath $zipPath -Force
        
        $zipSize = (Get-Item $zipPath).Length / 1MB
        Write-Host "[OK] Archive created: $zipPath ($(([math]::Round($zipSize, 2))) MB)"
    } catch {
        Write-Host "[WARN] Could not create zip archive: $_" -ForegroundColor Yellow
        Write-Host "   Files are still available in: $OutputFolder" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "[SUCCESS] EXPORT COMPLETE!"
Write-Host "========================================"
Write-Host ""
Write-Host "Export folder: $(Resolve-Path $OutputFolder)"
Write-Host "Share with your team and review: 00_EXPORT_SUMMARY.txt"
Write-Host ""
