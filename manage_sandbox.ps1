#!/usr/bin/env pwsh
<#
.DESCRIPTION
Valhalla Sandbox Service Management Script
Provides easy control over the persistent sandbox service
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "help")]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$serviceName = "SANDBOX_SERVICE.py"
$logFile = Join-Path $scriptPath "logs\sandbox_service.log"
$statusFile = Join-Path $scriptPath "sandbox_service_status.json"

function Show-Help {
    Write-Host @"
╔════════════════════════════════════════════════════════════╗
║         VALHALLA SANDBOX SERVICE MANAGEMENT               ║
╚════════════════════════════════════════════════════════════╝

Usage: .\manage_sandbox.ps1 -Action [action]

Actions:
  start     - Start the sandbox service in background
  stop      - Stop all running sandbox service processes
  restart   - Restart the sandbox service
  status    - Show current service status
  logs      - Display recent service logs
  help      - Show this help message

Examples:
  .\manage_sandbox.ps1 -Action start
  .\manage_sandbox.ps1 -Action status
  .\manage_sandbox.ps1 -Action logs
  .\manage_sandbox.ps1 -Action stop

"@
}

function Start-SandboxService {
    Write-Host "🚀 Starting Valhalla Sandbox Service..." -ForegroundColor Cyan
    
    # Check if already running
    $existing = Get-Process -Name python -ErrorAction SilentlyContinue | 
                Where-Object {$_.CommandLine -like "*SANDBOX_SERVICE*"}
    
    if ($existing) {
        Write-Host "⚠️  Sandbox service already running (PID: $($existing.Id))" -ForegroundColor Yellow
        return
    }
    
    # Start the service
    $process = Start-Process -FilePath python -ArgumentList $serviceName `
               -WorkingDirectory $scriptPath -WindowStyle Hidden -PassThru
    
    if ($process) {
        Write-Host "✅ Sandbox service started (PID: $($process.Id))" -ForegroundColor Green
        Start-Sleep -Seconds 2
        Show-ServiceStatus
    } else {
        Write-Host "❌ Failed to start sandbox service" -ForegroundColor Red
    }
}

function Stop-SandboxService {
    Write-Host "Stopping Valhalla Sandbox Service..." -ForegroundColor Cyan
    
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue | `
                 Where-Object {$_.CommandLine -like "*SANDBOX_SERVICE*"}
    
    if (-not $processes) {
        Write-Host "No sandbox service process found running" -ForegroundColor Yellow
        return
    }
    
    foreach ($proc in $processes) {
        Write-Host "  Stopping process $($proc.Id)..." -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Seconds 1
    Write-Host "✅ Sandbox service stopped" -ForegroundColor Green
}

function Restart-SandboxService {
    Write-Host "🔄 Restarting Valhalla Sandbox Service..." -ForegroundColor Cyan
    Stop-SandboxService
    Start-Sleep -Seconds 2
    Start-SandboxService
}

function Show-ServiceStatus {
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║             SANDBOX SERVICE STATUS                         ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue | 
                 Where-Object {$_.CommandLine -like "*SANDBOX_SERVICE*"}
    
    if ($processes) {
        Write-Host "Status: " -NoNewline -ForegroundColor Gray
        Write-Host "RUNNING ✓" -ForegroundColor Green
        Write-Host "Process ID: " -NoNewline -ForegroundColor Gray
        Write-Host "$($processes.Id)" -ForegroundColor Green
        Write-Host "Memory: " -NoNewline -ForegroundColor Gray
        Write-Host "$([math]::Round($processes.WorkingSet/1MB, 2)) MB" -ForegroundColor Green
        Write-Host "Started: " -NoNewline -ForegroundColor Gray
        Write-Host "$($processes.StartTime)" -ForegroundColor Green
    } else {
        Write-Host "Status: " -NoNewline -ForegroundColor Gray
        Write-Host "STOPPED" -ForegroundColor Red
    }
    
    if (Test-Path $statusFile) {
        Write-Host "`nLatest Status Report:" -ForegroundColor Cyan
        $content = Get-Content $statusFile | ConvertFrom-Json
        Write-Host "  Timestamp: $($content.timestamp)"
        Write-Host "  Service Status: $($content.service_status.status)"
        Write-Host "  Uptime: $($content.service_status.uptime_seconds)s"
        Write-Host "  Active Blocks: $($content.service_status.blocks_active)/30"
        Write-Host "  Health Checks: $($content.service_status.health_checks_passed)/$($content.service_status.total_health_checks)"
        Write-Host "  Components: $($content.total_components)"
        Write-Host "  Errors: $($content.service_status.errors_count)"
    }
    
    Write-Host ""
}

function Show-RecentLogs {
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          RECENT SANDBOX SERVICE LOGS (Last 20)            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    if (Test-Path $logFile) {
        $lines = @(Get-Content $logFile)
        $recent = $lines | Select-Object -Last 20
        
        foreach ($line in $recent) {
            if ($line -like "*INFO*") {
                Write-Host $line -ForegroundColor Green
            } elseif ($line -like "*WARNING*") {
                Write-Host $line -ForegroundColor Yellow
            } elseif ($line -like "*ERROR*") {
                Write-Host $line -ForegroundColor Red
            } else {
                Write-Host $line -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "No log file found" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Execute action
switch ($Action) {
    "start" {
        Start-SandboxService
    }
    "stop" {
        Stop-SandboxService
    }
    "restart" {
        Restart-SandboxService
    }
    "status" {
        Show-ServiceStatus
    }
    "logs" {
        Show-RecentLogs
    }
    "help" {
        Show-Help
    }
    default {
        Show-Help
    }
}
