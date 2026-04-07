# MONITORING THE 6-HOUR RUN

## Process Status
```powershell
# Check if running
Get-Process python -ErrorAction SilentlyContinue | Select-Object Name, Id, WorkingSet, UserProcessorTime

# Kill if needed (after 6 hours or on error)
Stop-Process -Name python -Force
```

## Export Growth (Every 60 seconds)
```powershell
# Count files
(Get-ChildItem ops/exports/*.csv -ErrorAction SilentlyContinue | Measure-Object).Count

# View recent 10 exports with timestamps
Get-ChildItem ops/exports/*.csv -ErrorAction SilentlyContinue | 
  Sort-Object LastWriteTime -Descending | 
  Select-Object -First 10 | 
  ForEach-Object { Write-Host "$(Get-Date $_.LastWriteTime -Format 'HH:mm:ss') - $($_.Name)" }
```

## Memory/CPU Usage
```powershell
# Get Python process details
Get-Process python -ErrorAction SilentlyContinue | 
  ForEach-Object { Write-Host "PID: $($_.Id) | Memory: $([math]::Round($_.WorkingSet/1MB, 1)) MB | CPU: $($_.CPU)s" }
```

## Log Errors (if available)
```powershell
# Check for error messages
if (Test-Path output.log) { 
  Get-Content output.log | Select-String -Pattern "ERROR|Exception|Traceback" | Select-Object -Last 20 
}
```

## Expected Metrics After 6 Hours

| Metric | Expected | Actual |
|--------|----------|--------|
| Total exports | ~720 | |
| Memory usage | 14-20 MB | |
| Duplicate filenames | 0 | |
| Last export time | Recent | |
| Process running | Yes | |

## Timeline

- **17:00:34 CST**: Process started (PID 1904)
- **18:11:03 CST**: Status check (61 min elapsed, 319 min remaining)
- **~23:00:34 CST**: Expected completion (6 hours = 360 min)

---

## ✅ Test SUCCESS Criteria

When the 6-hour run completes, verify:

1. **Process Status**:
   - [ ] Process still running OR cleanly exited
   - [ ] No segmentation faults or hard crashes
   - [ ] No zombie processes

2. **Export Quality**:
   - [ ] Exports continue every 30 seconds throughout
   - [ ] No duplicate filenames (each timestamp unique)
   - [ ] At least 700+ exports (1 per 30 sec over 6 hours)

3. **Resource Usage**:
   - [ ] Memory stays flat (~14 MB, no leaks)
   - [ ] CPU usage reasonable (not maxed)
   - [ ] No disk space issues

4. **Data Integrity**:
   - [ ] Sample exports have valid CSV format
   - [ ] Leads processed continuously
   - [ ] No obvious corruption in exports

---

## ❌ FAILURE Criteria (Stop immediately)

- Process crashes unexpectedly
- Memory usage grows beyond 100 MB (leak detection)
- Exports stop for more than 2 minutes
- Error rate visible in logs
- System unresponsive

---

**Note**: The 6-hour run is now operating in the background. You can close this terminal and check back periodically using the commands above. The process will continue running until manually stopped or system reboot.
