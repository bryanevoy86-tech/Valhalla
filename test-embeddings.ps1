# Test Auto-Embedding System
$api = "https://valhalla-api-ha6a.onrender.com/api"
$key = $env:HEIMDALL_BUILDER_API_KEY

if (-not $key) {
    Write-Host "Error: Set HEIMDALL_BUILDER_API_KEY first" -ForegroundColor Red
    exit 1
}

Write-Host "`nTesting Auto-Embedding System" -ForegroundColor Cyan
Write-Host "Test 1: Check coverage" -ForegroundColor Yellow
$response = curl.exe -s -X GET "$api/research/embeddings/stats" -H "X-API-Key: $key" | ConvertFrom-Json
Write-Host "  Total: $($response.total_docs), With embeddings: $($response.with_embeddings)`n" -ForegroundColor Green

Write-Host "Test 2: Generate embeddings" -ForegroundColor Yellow
$response = curl.exe -s -X POST "$api/jobs/research/embed_missing" -H "X-API-Key: $key" | ConvertFrom-Json
Write-Host "  Embedded: $($response.embedded) documents`n" -ForegroundColor Green

Write-Host "Test 3: Check coverage again" -ForegroundColor Yellow
$response = curl.exe -s -X GET "$api/research/embeddings/stats" -H "X-API-Key: $key" | ConvertFrom-Json
Write-Host "  Total: $($response.total_docs), With embeddings: $($response.with_embeddings)`n" -ForegroundColor Green

Write-Host "Done!" -ForegroundColor Green
