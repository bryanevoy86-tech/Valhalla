# Test Pack 75 (Heimdall↔Loki Sync Engine) and Pack 76 (Human Specialist Bridge)
# Usage: .\test_pack75_76.ps1

$baseUrl = "http://127.0.0.1:4000"

Write-Host "`n🧪 Testing Pack 75 - Heimdall↔Loki Sync Engine" -ForegroundColor Cyan

# Test 1: Clean sync (no conflict)
Write-Host "`n1️⃣  Testing CLEAN sync (both gods agree)..." -ForegroundColor Yellow
$cleanSync = @{
    subject_type = "deal"
    subject_reference = "deal_456"
    heimdall_payload = @{
        arv = 400000
        purchase_price = 250000
        cap_rate = 0.08
    }
    loki_payload = @{
        arv = 400000
        purchase_price = 250000
        cap_rate = 0.08
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/god-sync" -Method Post -ContentType "application/json" -Body $cleanSync
    Write-Host "✅ Clean sync created: $($response.id)" -ForegroundColor Green
    Write-Host "   Status: $($response.sync_status)" -ForegroundColor Green
    Write-Host "   Conflict: $($response.conflict_summary)" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

# Test 2: Conflict sync (gods disagree)
Write-Host "`n2️⃣  Testing CONFLICT sync (gods disagree on ARV)..." -ForegroundColor Yellow
$conflictSync = @{
    subject_type = "deal"
    subject_reference = "deal_789"
    heimdall_payload = @{
        arv = 400000
        purchase_price = 250000
        cap_rate = 0.08
    }
    loki_payload = @{
        arv = 350000  # Loki thinks ARV is lower
        purchase_price = 250000
        cap_rate = 0.08
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/god-sync" -Method Post -ContentType "application/json" -Body $conflictSync
    Write-Host "✅ Conflict sync created: $($response.id)" -ForegroundColor Green
    Write-Host "   Status: $($response.sync_status)" -ForegroundColor Yellow
    Write-Host "   Conflict summary:" -ForegroundColor Yellow
    Write-Host "   $($response.conflict_summary)" -ForegroundColor Yellow
    Write-Host "   Forwarded to case: $($response.forwarded_case_id)" -ForegroundColor Cyan
    
    $caseId = $response.forwarded_case_id
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

Write-Host "`n`n🧪 Testing Pack 76 - Human Specialist Bridge" -ForegroundColor Cyan

# Test 3: Create specialist (lawyer)
Write-Host "`n3️⃣  Creating human specialist (lawyer)..." -ForegroundColor Yellow
$specialist = @{
    name = "Sarah Chen"
    role = "lawyer"
    email = "sarah.chen@lawfirm.com"
    phone = "+1-555-0123"
    notes = "Real estate and contract specialist"
    expertise = @{
        areas = @("real estate law", "contracts", "compliance")
        years = 12
    }
} | ConvertTo-Json

try {
    $specialistResponse = Invoke-RestMethod -Uri "$baseUrl/specialists" -Method Post -ContentType "application/json" -Body $specialist
    Write-Host "✅ Specialist created: $($specialistResponse.id)" -ForegroundColor Green
    Write-Host "   Name: $($specialistResponse.name)" -ForegroundColor Green
    Write-Host "   Role: $($specialistResponse.role)" -ForegroundColor Green
    
    $specialistId = $specialistResponse.id
} catch {
    Write-Host "❌ Failed: $_" -ForegroundColor Red
}

# Test 4: Specialist adds comment to conflict case
if ($caseId -and $specialistId) {
    Write-Host "`n4️⃣  Specialist adding comment to conflict case..." -ForegroundColor Yellow
    $comment = @{
        comment = "I've reviewed the comps and agree with Loki's lower ARV estimate. Market has softened in this area."
        payload = @{
            recommendation = "use_conservative_arv"
            confidence = 0.85
            supporting_comps = @("123 Main St", "456 Oak Ave")
        }
    } | ConvertTo-Json
    
    try {
        $commentResponse = Invoke-RestMethod -Uri "$baseUrl/specialists/$specialistId/comment/$caseId" -Method Post -ContentType "application/json" -Body $comment
        Write-Host "✅ Comment added: $($commentResponse.id)" -ForegroundColor Green
        Write-Host "   Specialist: $($commentResponse.specialist_id)" -ForegroundColor Green
        Write-Host "   Case: $($commentResponse.case_id)" -ForegroundColor Green
        Write-Host "   Comment: $($commentResponse.comment)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed: $_" -ForegroundColor Red
    }
    
    # Test 5: Verify event was added to God case
    Write-Host "`n5️⃣  Verifying event added to God case..." -ForegroundColor Yellow
    try {
        $events = Invoke-RestMethod -Uri "$baseUrl/god-cases/$caseId/events" -Method Get
        $humanEvents = $events | Where-Object { $_.actor -eq "human" }
        Write-Host "✅ Found $($humanEvents.Count) human event(s) in case timeline" -ForegroundColor Green
        foreach ($event in $humanEvents) {
            Write-Host "   - [$($event.event_type)] $($event.message)" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "❌ Failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n`n📊 Summary:" -ForegroundColor Cyan
Write-Host "Pack 75: Heimdall↔Loki sync engine detects conflicts and auto-creates review cases" -ForegroundColor White
Write-Host "Pack 76: Human specialists can comment on cases and events sync to God timeline" -ForegroundColor White
Write-Host "`nWorkflow: Heimdall proposes → Loki critiques → System detects conflict → Human expert weighs in → You decide" -ForegroundColor Green
