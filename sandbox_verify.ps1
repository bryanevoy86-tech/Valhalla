# SANDBOX Enforcement Verification Script
# Windows PowerShell
# 
# Tests that SANDBOX blocks all outbound effects and ACTIVE allows them.
#
# Usage:
#   $env:BASE_URL = "http://localhost:8000"
#   .\sandbox_verify.ps1

$ErrorActionPreference = "Stop"

$BASE = $env:BASE_URL
if (-not $BASE) { $BASE = "http://localhost:8000" }

Write-Host "BASE_URL=$BASE`n" -ForegroundColor Cyan

function PostJson($path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 8
  return Invoke-RestMethod -Method Post -Uri "$BASE$path" -ContentType "application/json" -Body $json
}

function TryPost($path, $obj) {
  try {
    $r = PostJson $path $obj
    return @{ ok=$true; result=$r }
  } catch {
    $status = $_.Exception.Response.StatusCode.value__
    $body = ""
    try {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $body = $reader.ReadToEnd()
    } catch {}
    return @{ ok=$false; status=$status; body=$body }
  }
}

Write-Host "1) Set engine state to SANDBOX" -ForegroundColor Yellow
$res = TryPost "/api/engines/transition" @{ engine_name="wholesaling"; target_state="SANDBOX" }
if ($res.ok) {
  Write-Host "  ✓ Transitioned to SANDBOX" -ForegroundColor Green
  $res.result | ConvertTo-Json -Depth 4 | Out-Host
} else {
  Write-Host "  ✗ Transition failed (status $($res.status))" -ForegroundColor Red
  $res.body | Out-Host
}

Write-Host "`n2) Check runbook status" -ForegroundColor Yellow
try {
  $status = Invoke-RestMethod -Method Get -Uri "$BASE/api/runbook/status"
  Write-Host "  Runbook status:" -ForegroundColor Cyan
  $status | ConvertTo-Json -Depth 8 | Out-Host
} catch {
  Write-Host "  ✗ Runbook error: $_" -ForegroundColor Red
}

Write-Host "`n3) SANDBOX block test: These MUST return 409 EngineBlocked" -ForegroundColor Yellow
$tests = @(
  @{ name="send-email"; path="/messaging/send-email"; body=@{ to="test@example.com"; subject="Test"; body="Test" } },
  @{ name="send-sms"; path="/messaging/send-sms"; body=@{ to="+15555555555"; message="Test" } },
  @{ name="notify-webhook"; path="/notify/webhook"; body=@{ url="https://example.com/webhook"; payload=@{ hello="world" } } },
  @{ name="docs-send"; path="/docs/send"; body=@{ request=@{ generated_doc_id=1; recipients=@() } } },
  @{ name="legal-sign"; path="/legal/sign"; body=@{ document_id=1; signer_name="Test"; signer_email="test@example.com" } },
  @{ name="alerts-test"; path="/admin/heimdall/api/alerts/test"; body=@{} }
)

$blocked_count = 0
foreach ($t in $tests) {
  $res = TryPost $t.path $t.body
  if ($res.ok) {
    Write-Host "  ✗ $($t.name) was ALLOWED in SANDBOX (should be blocked!)" -ForegroundColor Red
  } else {
    if ($res.status -eq 409) {
      Write-Host "  ✓ $($t.name) blocked with 409" -ForegroundColor Green
      $blocked_count++
    } else {
      Write-Host "  ⚠ $($t.name) returned $($res.status) (expected 409)" -ForegroundColor Yellow
      Write-Host "    Body: $($res.body)" -ForegroundColor DarkYellow
    }
  }
}

Write-Host "`nSANDBOX Block Summary: $blocked_count/$($tests.Count) endpoints blocked" -ForegroundColor Cyan

Write-Host "`n4) Transition to ACTIVE and retest" -ForegroundColor Yellow
$res = TryPost "/api/engines/transition" @{ engine_name="wholesaling"; target_state="ACTIVE" }
if ($res.ok) {
  Write-Host "  ✓ Transitioned to ACTIVE" -ForegroundColor Green
  
  Write-Host "`n5) ACTIVE allow test: These should now proceed (if no other gates block)" -ForegroundColor Yellow
  $active_count = 0
  foreach ($t in $tests) {
    $res = TryPost $t.path $t.body
    if ($res.ok) {
      Write-Host "  ✓ $($t.name) allowed in ACTIVE" -ForegroundColor Green
      $active_count++
    } else {
      if ($res.status -eq 409) {
        Write-Host "  ⚠ $($t.name) still blocked by 409 (may be policy/gates)" -ForegroundColor Yellow
      } else {
        Write-Host "  ✓ $($t.name) not blocked by engine (status $($res.status))" -ForegroundColor Green
      }
    }
  }
  Write-Host "`nACTIVE Allow Summary: $active_count endpoints allowed" -ForegroundColor Cyan
} else {
  Write-Host "  ✗ Transition to ACTIVE failed (status $($res.status))" -ForegroundColor Red
  $res.body | Out-Host
}

Write-Host "`n✅ Verification complete." -ForegroundColor Green
Write-Host "   If all SANDBOX blocks passed, engine guards are working." -ForegroundColor Cyan
