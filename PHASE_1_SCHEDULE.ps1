#!/usr/bin/env pwsh
<#
.SYNOPSIS
PHASE 1 SCHEDULER
Creates a Windows scheduled task to run the baseline monitor
Can be set to run now or at a specific time

.PARAMETER StartNow
If true, runs Phase 1 immediately. If false, schedules for later.

.PARAMETER ScheduleTime
If StartNow is false, specify time as HH:mm (e.g., "23:30" for 11:30 PM)

.EXAMPLE
.\PHASE_1_SCHEDULE.ps1 -StartNow $true
Runs Phase 1 baseline monitor immediately

.\PHASE_1_SCHEDULE.ps1 -StartNow $false -ScheduleTime "22:00"
Schedules Phase 1 to run at 10:00 PM tonight
#>

param(
    [bool]$StartNow = $true,
    [string]$ScheduleTime = ""
)

$VALHALLA_ROOT = "C:\dev\valhalla"
$MONITOR_SCRIPT = "$VALHALLA_ROOT\PHASE_1_BASELINE_MONITOR.ps1"

Write-Host "╔════════════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                       PHASE 1 BASELINE SCHEDULER                              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verify script exists
if (-not (Test-Path $MONITOR_SCRIPT)) {
    Write-Host "ERROR: Monitor script not found: $MONITOR_SCRIPT" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Monitor script found: $MONITOR_SCRIPT" -ForegroundColor Green
Write-Host ""

if ($StartNow) {
    Write-Host "Starting Phase 1 Baseline Monitor immediately..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "⏱️  Duration: 6 hours" -ForegroundColor Cyan
    Write-Host "📊 Checkpoints: Every 2 hours" -ForegroundColor Cyan
    Write-Host "📝 Output: PHASE_1_baseline_report_*.txt" -ForegroundColor Cyan
    Write-Host ""
    
    # Run the monitor
    & powershell.exe -NoExit -File $MONITOR_SCRIPT -DurationMinutes 360 -IntervalMinutes 120
}
else {
    if (-not $ScheduleTime) {
        Write-Host "ERROR: ScheduleTime required when StartNow is false" -ForegroundColor Red
        Write-Host "Usage: .\PHASE_1_SCHEDULE.ps1 -StartNow \$false -ScheduleTime '22:00'" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Scheduling Phase 1 Baseline Monitor for: $ScheduleTime" -ForegroundColor Yellow
    Write-Host ""
    
    # Create scheduled task
    $TaskName = "Valhalla-Phase1-Baseline"
    $TaskPath = "\Valhalla\"
    
    # Remove existing task if present
    try {
        Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "✓ Existing task cleared" -ForegroundColor Green
    }
    catch {}
    
    # Create new task
    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoExit -File '$MONITOR_SCRIPT' -DurationMinutes 360 -IntervalMinutes 120"
    
    $Trigger = New-ScheduledTaskTrigger -Daily -At $ScheduleTime
    
    $Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest
    
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
    
    Write-Host "✓ Scheduled task created: $TaskName" -ForegroundColor Green
    Write-Host "✓ Path: $TaskPath" -ForegroundColor Green
    Write-Host "✓ Scheduled for: $ScheduleTime daily" -ForegroundColor Green
    Write-Host ""
    Write-Host "To view scheduled tasks:" -ForegroundColor Cyan
    Write-Host "  Get-ScheduledTask -TaskName 'Valhalla-Phase1-Baseline'" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "PHASE 1 SCHEDULED" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
