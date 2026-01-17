param([string]$BaseUrl = "http://localhost:8000")

Write-Host ""
Write-Host "====== VALHALLA SYSTEM STAGE CHECK ======"
Write-Host "Base URL: $BaseUrl"
Write-Host ""

function Call($label, $method, $url, $body=$null) {
    Write-Host "---- $label ----"
    try {
        if ($body) {
            $json = $body | ConvertTo-Json -Depth 10
            $res = Invoke-RestMethod -Method $method -Uri $url -ContentType "application/json" -Body $json -TimeoutSec 15
        } else {
            $res = Invoke-RestMethod -Method $method -Uri $url -TimeoutSec 15
        }
        $res | ConvertTo-Json -Depth 10
        return $res
    } catch {
        Write-Host "FAILED: $($_.Exception.Message)"
        if ($_.ErrorDetails) { Write-Host $_.ErrorDetails.Message }
        return $null
    }
}

# API Health
Call "API Health" "GET" "$BaseUrl/docs" | Out-Null

# Runbook Status
$runbook = Call "Runbook Status" "GET" "$BaseUrl/api/governance/runbook/status"

if ($runbook) {
    Write-Host ""
    Write-Host "---- RUNBOOK SUMMARY ----"
    Write-Host "Blockers: $($runbook.blockers.Count)"
    Write-Host "Warnings: $($runbook.warnings.Count)"
    Write-Host "OK to Go Live: $($runbook.ok_to_enable_go_live)"
}

Write-Host ""
Write-Host "====== STAGE CHECK COMPLETE ======"
Write-Host ""

if ($runbook) {
    if ($runbook.blockers.Count -eq 0) {
        Write-Host "STATUS: SYSTEM FUNCTIONAL AT CURRENT STAGE"
    } else {
        Write-Host "STATUS: SYSTEM BLOCKED FROM GO-LIVE"
        Write-Host "Review RUNBOOK BLOCKERS above."
    }
} else {
    Write-Host "STATUS: GOVERNANCE NOT RESPONDING"
}
