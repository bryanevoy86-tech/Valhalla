# Heimdall Research Core - Complete Test Script
# Run this after: docker-compose up -d --build api

Write-Host "🔍 Heimdall Research Core Test Suite" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$api = "http://localhost:8000/api"
$key = "test123"  # Replace with your HEIMDALL_BUILDER_API_KEY from .env

Write-Host "📡 Step 1: Testing API Health..." -ForegroundColor Yellow
$health = curl.exe -s "$api/healthz" | ConvertFrom-Json
Write-Host "Health: $($health | ConvertTo-Json -Compress)" -ForegroundColor Green
Write-Host ""

Write-Host "🔑 Step 2: Verifying Research API Key..." -ForegroundColor Yellow
$keysTest = curl.exe -s "$api/research/keys" -H "X-API-Key: $key" | ConvertFrom-Json
Write-Host "Keys Test: $($keysTest | ConvertTo-Json -Compress)" -ForegroundColor Green
Write-Host ""

Write-Host "📚 Step 3: Adding FastAPI Documentation Source..." -ForegroundColor Yellow
$source1 = curl.exe -s -X POST "$api/research/sources" `
  -H "X-API-Key: $key" `
  -H "Content-Type: application/json" `
  -d '{"name":"FastAPI Docs","url":"https://fastapi.tiangolo.com/","kind":"web","ttl_seconds":86400,"enabled":true}' | ConvertFrom-Json
Write-Host "Source 1 ID: $($source1.id) - $($source1.name)" -ForegroundColor Green
Write-Host ""

Write-Host "📘 Step 4: Adding SQLAlchemy Documentation Source..." -ForegroundColor Yellow
$source2 = curl.exe -s -X POST "$api/research/sources" `
  -H "X-API-Key: $key" `
  -H "Content-Type: application/json" `
  -d '{"name":"SQLAlchemy Docs","url":"https://docs.sqlalchemy.org/en/20/","kind":"web","ttl_seconds":86400,"enabled":true}' | ConvertFrom-Json
Write-Host "Source 2 ID: $($source2.id) - $($source2.name)" -ForegroundColor Green
Write-Host ""

Write-Host "📋 Step 5: Listing All Sources..." -ForegroundColor Yellow
$sources = curl.exe -s "$api/research/sources" -H "X-API-Key: $key" | ConvertFrom-Json
Write-Host "Total Sources: $($sources.Count)" -ForegroundColor Green
foreach ($src in $sources) {
    Write-Host "  - ID $($src.id): $($src.name) ($($src.url))" -ForegroundColor White
}
Write-Host ""

Write-Host "🧠 Step 6: Ingesting FastAPI Docs (source_id=$($source1.id))..." -ForegroundColor Yellow
$ingest1 = curl.exe -s -X POST "$api/research/ingest" `
  -H "X-API-Key: $key" `
  -H "Content-Type: application/json" `
  -d "{`"source_id`":$($source1.id)}" | ConvertFrom-Json
Write-Host "Ingest Result: $($ingest1.message)" -ForegroundColor Green
Write-Host ""

Write-Host "🧠 Step 7: Ingesting SQLAlchemy Docs (source_id=$($source2.id))..." -ForegroundColor Yellow
$ingest2 = curl.exe -s -X POST "$api/research/ingest" `
  -H "X-API-Key: $key" `
  -H "Content-Type: application/json" `
  -d "{`"source_id`":$($source2.id)}" | ConvertFrom-Json
Write-Host "Ingest Result: $($ingest2.message)" -ForegroundColor Green
Write-Host ""

Write-Host "🔍 Step 8: Querying for 'Response Model'..." -ForegroundColor Yellow
$query1 = curl.exe -s -X POST "$api/research/query" `
  -H "X-API-Key: $key" `
  -H "Content-Type: application/json" `
  -d '{"q":"Response Model","limit":3}' | ConvertFrom-Json
Write-Host "Query Results: $($query1.result_count) matches found" -ForegroundColor Green
foreach ($result in $query1.results) {
    Write-Host "  - $($result.source_name): $($result.snippet.Substring(0, [Math]::Min(100, $result.snippet.Length)))..." -ForegroundColor White
}
Write-Host ""

Write-Host "📖 Step 9: Adding Builder Safety Rules Playbook..." -ForegroundColor Yellow
$playbook1 = curl.exe -s -X POST "$api/playbooks" `
  -H "X-API-Key: $key" `
  -H "Content-Type: application/json" `
  -d '{"slug":"builder-safety-rules","title":"Builder Safety Rules","body_md":"1. Only write inside approved directories.\n2. Keep file size under 200 KB.\n3. Use dry-run before approve=true.\n4. Always commit with clear message.","enabled":true}' | ConvertFrom-Json
Write-Host "Playbook Created: $($playbook1.title) (slug: $($playbook1.slug))" -ForegroundColor Green
Write-Host ""

Write-Host "📚 Step 10: Listing All Playbooks..." -ForegroundColor Yellow
$playbooks = curl.exe -s "$api/playbooks" | ConvertFrom-Json
Write-Host "Total Playbooks: $($playbooks.Count)" -ForegroundColor Green
foreach ($pb in $playbooks) {
    Write-Host "  - $($pb.title) ($($pb.slug))" -ForegroundColor White
}
Write-Host ""

Write-Host "✅ HEIMDALL RESEARCH CORE IS READY!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Open browser: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  2. Explore /research/sources, /research/query, /playbooks" -ForegroundColor White
Write-Host "  3. Add more sources and playbooks as needed" -ForegroundColor White
Write-Host ""
Write-Host "🔮 Optional: Set up nightly auto-ingest job for continuous learning" -ForegroundColor Yellow
