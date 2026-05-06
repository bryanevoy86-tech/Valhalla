# Phase 3 Backend Smoke Test

param([string]$BaseUrl = "http://127.0.0.1:4000")

$passed = 0
$failed = 0
$errors = @()

function Test-Endpoint {
    param([string]$Name, [string]$Method, [string]$Path)
    Write-Host "  Testing: $Name..." -NoNewline
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri "$BaseUrl$Path" -Method Get -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Uri "$BaseUrl$Path" -Method Post -ErrorAction Stop
        }
        Write-Host " OK" -ForegroundColor Green
        $global:passed++
        return $true
    }
    catch {
        $msg = $_.Exception.Message.Split("`n")[0]
        Write-Host " FAIL: $msg" -ForegroundColor Red
        $global:failed++
        return $false
    }
}

Write-Host "`n========== PHASE 3 BACKEND SMOKE TEST ==========" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl`n" -ForegroundColor Cyan

Write-Host "System Status:" -ForegroundColor Yellow
Test-Endpoint "Go-Live" "GET" "/api/go-live/status"
Test-Endpoint "Health" "GET" "/health"

Write-Host "`nVA Intake:" -ForegroundColor Yellow
Test-Endpoint "List Leads" "GET" "/api/va-intake/leads"
Test-Endpoint "Pending Approvals" "GET" "/api/va-intake/approvals/pending"

Write-Host "`nDev Endpoints:" -ForegroundColor Yellow
Test-Endpoint "Duplicate Check" "GET" "/api/dev/duplicate-check"

Write-Host "`nAPI Docs:" -ForegroundColor Yellow
Test-Endpoint "Swagger" "GET" "/docs"
Test-Endpoint "OpenAPI" "GET" "/openapi.json"

Write-Host "`n========== SUMMARY ==========" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Total:  $($passed + $failed)"
if ($failed -eq 0) { Write-Host "`nAll tests passed!" -ForegroundColor Green }
Write-Host "================================================`n" -ForegroundColor Cyan
