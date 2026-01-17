# SANDBOX REAL DATA INGESTION - QUICK START CHECKLIST

## Pre-Flight Checklist

### Environment Setup
- [x] Python 3.13 environment configured
- [x] Virtual environment activated
- [x] All required packages installed
- [x] Sandbox service running (persistent mode)
- [x] CSV ingestion module deployed

### CSV File Preparation
- [ ] CSV file created/updated with real leads
- [ ] Columns present: name, email, value, location, phone
- [ ] Required fields filled: name, email, value
- [ ] Email format valid (contains @ and .)
- [ ] Values are positive numbers
- [ ] File saved in valhalla directory (or update path)

### Configuration
- [ ] CSV file path verified in continuous_ingestion.py
- [ ] Interval set (default 30 seconds - RECOMMENDED)
- [ ] Max cycles decided (unlimited or specific number)
- [ ] Dry-run mode enabled in sandbox (SAFETY CHECK)
- [ ] Risk monitoring configured and active

---

## Running Continuous Ingestion

### Option 1: Simple Start (Recommended)
```bash
# 1. Open PowerShell in valhalla directory
# 2. Activate environment
.\.venv\Scripts\Activate.ps1

# 3. Run continuous ingestion
python continuous_ingestion.py

# 4. Observe console output (Ctrl+C to stop)
```

### Option 2: Test Run First
```python
# Run exactly 3 cycles to test before full deployment
from continuous_ingestion import ContinuousDataIngestion

ing = ContinuousDataIngestion("real_leads.csv", interval=5)
ing.run_continuous(max_cycles=3)
```

### Option 3: Sandbox Integration
```bash
python sandbox_real_data_integration.py
```

---

## Monitoring During Ingestion

### Real-Time Console Output
```
[2026-01-07 19:12:28] [CYCLE 1] Starting ingestion cycle...
[PROCESSING] 10 leads being validated and processed...
[OK] Cycle 1 complete: 10 leads ingested in 0.00s
  ├─ Total ingested: 10
  ├─ Valid leads: 10
  ├─ Success rate: 100.0%
  └─ Uptime: 0h 0m 5s
```

### Open Dashboard (In New Terminal)
```bash
python show_ops_cockpit.py
```

### Check Statistics File
```bash
# View ingestion stats
type logs\continuous_ingestion_stats.json

# View risk assessment
type logs\risk_monitoring_results.json
```

---

## Cycle Behavior

### Each 30-Second Cycle Does:
1. **Read CSV** → Load all records from file
2. **Validate** → Check name, email, value fields
3. **Sanitize** → Clean whitespace, format data
4. **Process** → Run through 6-step pipeline
5. **Assess Risk** → Check data quality and security
6. **Log Results** → Save statistics to JSON

### Success Indicators
- ✓ Console shows lead names being processed
- ✓ All fields validated without errors
- ✓ 6 pipeline stages completed per lead
- ✓ Uptime counter increases each cycle
- ✓ Statistics saved to logs/continuous_ingestion_stats.json

---

## Stopping Ingestion

### Graceful Stop
```
Press Ctrl+C in the terminal
```

The system will:
1. Complete the current cycle
2. Generate final report
3. Save statistics
4. Display summary
5. Exit cleanly

### Expected Final Output
```
[STOPPED] Continuous ingestion stopped by user
[FINAL REPORT]
  Total Cycles: N
  Total Leads: N*10
  Valid Leads: N*10
  Uptime: Nh 0m 0s
  Status: STOPPED
  Report saved to: logs/continuous_ingestion_stats.json
```

---

## Verification Checklist

After starting ingestion, verify:

- [ ] Console shows "[STARTING] CSV Ingestion" message
- [ ] Lead names appear in console output
- [ ] All 6 pipeline stages shown: ✓ 1/6, ✓ 2/6, etc.
- [ ] Cycle counter increments each interval
- [ ] "Uptime" increases on screen
- [ ] No ERROR messages in red text
- [ ] logs/continuous_ingestion_stats.json updates

---

## Configuration Reference

### Default Settings (No Changes Required)
```python
csv_path = "real_leads.csv"          # File to ingest
interval = 30                        # Seconds between cycles
max_cycles = None                    # Unlimited cycles
dry_run = True                       # Sandbox protection ENABLED
monitoring = True                    # Risk monitoring ENABLED
```

### Custom Settings
```python
# Example: Custom interval and max cycles
from continuous_ingestion import ContinuousDataIngestion

ing = ContinuousDataIngestion(
    csv_path="my_file.csv",          # Your CSV file
    interval=60                      # Every 60 seconds
)
ing.run_continuous(max_cycles=100)   # Stop after 100 cycles
```

---

## Troubleshooting

### Issue: "CSV file not found"
**Solution:** 
- Check file is in valhalla directory
- Or update csv_path in continuous_ingestion.py
- Path must be exact (check for typos)

### Issue: "Invalid email format"
**Solution:**
- Email must have @ and . (e.g., john@example.com)
- Check for spaces or special characters

### Issue: "Value must be numeric"
**Solution:**
- Remove $ signs, commas
- Use plain numbers: 500000 (not $500,000)

### Issue: Script stops after first cycle
**Solution:**
- Check for KeyboardInterrupt (you pressed Ctrl+C)
- Check logs/ for error messages
- Run with max_cycles=3 first to test

### Issue: Memory/CPU usage high
**Solution:**
- Reduce interval (speed up cycles)
- Reduce max_cycles (stop sooner)
- Check CSV file size (should be < 10MB)

---

## Quick Commands

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Start continuous ingestion
python continuous_ingestion.py

# Test with 3 cycles
python -c "from continuous_ingestion import *; ContinuousDataIngestion('real_leads.csv', 5).run_continuous(3)"

# View latest stats
Get-Content logs\continuous_ingestion_stats.json

# Check sandbox status
python sandbox_controller.py status

# View ops dashboard
python show_ops_cockpit.py

# Stop (in running terminal)
# Press Ctrl+C
```

---

## Expected Timeline

```
Time          Action                          Status
--            Prepare CSV file               [Setup]
--            Run script                     [Start]
0:00-0:30     Cycle 1 processing             [Running]
0:30-1:00     Cycle 2 processing             [Running]
1:00-1:30     Cycle 3 processing             [Running]
...
Ctrl+C        Stop ingestion                 [Stopped]
--            View final statistics          [Complete]
```

---

## System Status

### Current Status
```
Sandbox:              RUNNING (persistent)
Continuous Module:    READY (tested)
Dry-Run Protection:   ENABLED (safe)
Risk Monitoring:      ACTIVE
CSV Validation:       ENABLED
6-Step Pipeline:      OPERATIONAL
```

### Performance Expectations
- **Leads per cycle:** ~10 (depends on CSV)
- **Cycle time:** < 1 second
- **Memory overhead:** < 50MB
- **CPU usage:** < 5% during cycles
- **Dry-run protection:** Prevents real data issues

---

## Next Steps

1. **Prepare CSV** - Add your real leads to real_leads.csv
2. **Verify Setup** - Check all checklist items above
3. **Run Test** - Execute with max_cycles=3 first
4. **Review Logs** - Check for any errors in output
5. **Start Production** - Run without max_cycles limit
6. **Monitor** - Watch console and dashboard

---

## Support Files

| File | Purpose |
|------|---------|
| continuous_ingestion.py | Main ingestion engine |
| sandbox_real_data_integration.py | Setup script |
| csv_ingestion.py | CSV reader/validator |
| real_leads.csv | Sample/test data |
| logs/continuous_ingestion_stats.json | Ingestion statistics |
| show_ops_cockpit.py | Real-time dashboard |

---

**Status: READY TO RUN**
**Protection: DRY-RUN MODE ENABLED**
**Monitoring: ACTIVE**

Your sandbox is configured for continuous real data ingestion. Start with the Quick Start command above!
