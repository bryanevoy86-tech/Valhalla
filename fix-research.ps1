# Fix Valhalla Research Endpoints
# This script diagnoses and fixes the research router import issues

$api = "https://valhalla-api-ha6a.onrender.com/api"
$key = $env:HEIMDALL_BUILDER_API_KEY

if (-not $key) {
    Write-Host "Error: Set HEIMDALL_BUILDER_API_KEY environment variable first" -ForegroundColor Red
    Write-Host 'Example: $env:HEIMDALL_BUILDER_API_KEY = "your-key-here"' -ForegroundColor Yellow
    exit 1
}

Write-Host "`n=== Valhalla Research Fix ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check database tables
Write-Host "Step 1: Checking database tables..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$api/admin/db/check" -Method Get -Headers @{"X-Admin-Key"=$key}
    Write-Host "  Tables found: $($response.research_tables_exist -join ', ')" -ForegroundColor Green
    Write-Host "  Count: $($response.research_tables_count) / $($response.expected_tables)" -ForegroundColor Green
    Write-Host "  Alembic version: $($response.alembic_version)" -ForegroundColor Green
    
    if ($response.all_tables_exist) {
        Write-Host "  Status: All research tables exist!" -ForegroundColor Green
    } else {
        Write-Host "  Status: Missing tables - need to run migration" -ForegroundColor Red
        $needsMigration = $true
    }
    Write-Host ""
}
catch {
    Write-Host "  Error checking database: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Admin endpoint might not be deployed yet. Wait 1-2 minutes." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Step 2: Run migration if needed
if ($needsMigration) {
    Write-Host "Step 2: Running database migration..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "$api/admin/migrate" -Method Post -Headers @{"X-Admin-Key"=$key}
        if ($response.ok) {
            Write-Host "  Migration successful!" -ForegroundColor Green
            Write-Host "  Output: $($response.stdout)" -ForegroundColor Cyan
        } else {
            Write-Host "  Migration failed!" -ForegroundColor Red
            Write-Host "  Error: $($response.stderr)" -ForegroundColor Red
        }
        Write-Host ""
    }
    catch {
        Write-Host "  Error running migration: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
} else {
    Write-Host "Step 2: Migration not needed - tables already exist" -ForegroundColor Green
    Write-Host ""
}

# Step 3: Test research endpoints
Write-Host "Step 3: Testing research endpoints..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$api/research/keys" -Method Get -Headers @{"X-API-Key"=$key}
    Write-Host "  Research keys endpoint: OK" -ForegroundColor Green
}
catch {
    Write-Host "  Research keys endpoint: NOT AVAILABLE" -ForegroundColor Red
    Write-Host "  Note: You may need to restart the Render service for imports to refresh" -ForegroundColor Yellow
}

try {
    $response = Invoke-RestMethod -Uri "$api/research/embeddings/stats" -Method Get -Headers @{"X-API-Key"=$key}
    Write-Host "  Embeddings stats endpoint: OK" -ForegroundColor Green
    Write-Host "    Total docs: $($response.total_docs)" -ForegroundColor Cyan
    Write-Host "    With embeddings: $($response.with_embeddings)" -ForegroundColor Cyan
}
catch {
    Write-Host "  Embeddings stats endpoint: NOT AVAILABLE" -ForegroundColor Red
}

try {
    $response = Invoke-RestMethod -Uri "$api/jobs/research/embed_missing" -Method Post -Headers @{"X-API-Key"=$key; "Content-Type"="application/json"}
    Write-Host "  Embedding job endpoint: OK" -ForegroundColor Green
}
catch {
    Write-Host "  Embedding job endpoint: NOT AVAILABLE" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If endpoints are still not available after migration:" -ForegroundColor Yellow
Write-Host "  1. Go to Render Dashboard" -ForegroundColor White
Write-Host "  2. Select valhalla-api service" -ForegroundColor White
Write-Host "  3. Click 'Manual Deploy' -> 'Clear build cache & deploy'" -ForegroundColor White
Write-Host "  OR restart the service to reload Python imports" -ForegroundColor White
Write-Host ""
Write-Host "Then run this script again to verify." -ForegroundColor Yellow
Write-Host ""
