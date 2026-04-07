# HOW TO RUN CONTINUOUS REAL DATA INGESTION - SANDBOX

## The Short Version (Just Run This)

### Step 1: Open PowerShell

Navigate to your valhalla directory:
```powershell
cd c:\dev\valhalla
```

### Step 2: Activate Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Run Continuous Ingestion

**Option A - Full Production (Unlimited)**
```powershell
python continuous_ingestion.py
```

This will:
- Read real_leads.csv every 30 seconds
- Process all leads through 6-step pipeline
- Run forever until you press Ctrl+C
- Save statistics to logs/continuous_ingestion_stats.json

**Option B - Test First (3 Cycles)**
```powershell
python -c "from continuous_ingestion import ContinuousDataIngestion; ContinuousDataIngestion('real_leads.csv', interval=5).run_continuous(max_cycles=3)"
```

This will:
- Run exactly 3 ingestion cycles
- Use 5-second intervals (faster testing)
- Stop automatically after 3 cycles
- Takes about 15 seconds total

**Option C - Custom Duration (30 Cycles)**
```powershell
python -c "from continuous_ingestion import ContinuousDataIngestion; ContinuousDataIngestion('real_leads.csv').run_continuous(max_cycles=30)"
```

This will:
- Run exactly 30 cycles (15 minutes at 30s interval)
- Process 300 leads total
- Stop automatically
- Takes about 15 minutes

### Step 4: Watch the Output

You'll see real-time output like:

```
[2026-01-07 19:12:28] [CYCLE 1] Starting ingestion cycle...
[PROCESSING] John Doe - john@example.com
  ✓ 1/6 A/B Test Tracking: PROCESSED
  ✓ 2/6 Script Promotion: PROCESSED
  ✓ 3/6 Deal Packet: PROCESSED
  ✓ 4/6 Outcome Evaluation: PROCESSED
  ✓ 5/6 Clone Readiness: PROCESSED
  ✓ 6/6 Lead Scoring: PROCESSED

[PROCESSING] Jane Smith - jane@example.com
  ✓ 1/6 A/B Test Tracking: PROCESSED
  [... more leads ...]

[2026-01-07 19:12:28] [OK] Cycle 1 complete: 10 leads ingested in 0.00s
  Statistics:
    Cycles: 1
    Total leads: 10
    Valid leads: 10
    Uptime: 0h 0m 5s
```

### Step 5: Stop (If Running Unlimited)

Press **Ctrl+C** in the terminal

You'll see:

```
[STOPPED] Continuous ingestion stopped by user
[FINAL REPORT]
  Total Cycles: 10
  Total Leads Ingested: 100
  Valid Leads: 100
  Invalid Leads: 0
  Average Leads/Cycle: 10.0
  Total Uptime: 305.2s
  Status: STOPPED
  Report saved to: logs/continuous_ingestion_stats.json
```

---

## What's Happening Behind The Scenes

### Each 30-Second Cycle

1. **Reads CSV file** (real_leads.csv)
2. **Validates each lead** (name, email, value required)
3. **Cleans the data** (trims, lowercases, formats)
4. **Processes through 6-step pipeline:**
   - A/B Test Tracking
   - Script Promotion
   - Deal Packet Generation
   - Outcome Evaluation
   - Clone Readiness
   - Lead Scoring
5. **Checks risk level** (data quality, security)
6. **Saves statistics** to JSON file

### After Ctrl+C

Final report is generated showing:
- How many cycles completed
- Total leads processed
- Valid vs invalid counts
- Total runtime
- Statistics file location

---

## Viewing Results While Running

### Option 1: Another PowerShell Window (While it's running)

```powershell
# View live statistics file
Get-Content logs\continuous_ingestion_stats.json | ConvertFrom-Json | Format-List

# View in real-time (updates every 2 seconds)
$timer = New-Object Timers.Timer
$timer.Interval = 2000
$action = { Get-Content logs\continuous_ingestion_stats.json }
Register-ObjectEvent -InputObject $timer -EventName Elapsed -Action $action | Out-Null
$timer.Start()

# Stop watching: Press Ctrl+C
```

### Option 2: Dashboard (New Window)

```powershell
# In a new PowerShell window
python show_ops_cockpit.py
```

This shows:
- Sandbox status
- Number of cycles
- Leads processed
- Data quality
- Risk alerts

### Option 3: View File Directly

```powershell
# After ingestion stops
type logs\continuous_ingestion_stats.json
```

---

## Example: 1-Hour Continuous Ingestion

```powershell
# 30-second interval × 120 cycles = 60 minutes
python -c "from continuous_ingestion import ContinuousDataIngestion; ContinuousDataIngestion('real_leads.csv', interval=30).run_continuous(max_cycles=120)"

# Results:
# - Processes 1,200 leads (120 cycles × 10 leads/cycle)
# - Takes approximately 60 minutes
# - Saves detailed statistics
# - Monitors risk the entire time
```

---

## Example: Fast Testing (5 Leads per Cycle, 5 Cycles)

```powershell
# Modify CSV to have 5 records, then:
python -c "from continuous_ingestion import ContinuousDataIngestion; ContinuousDataIngestion('real_leads.csv', interval=1).run_continuous(max_cycles=5)"

# Results:
# - Processes 25 leads (5 cycles × 5 leads/cycle)
# - Takes approximately 5 seconds
# - 1-second interval between cycles (fast)
# - Great for testing
```

---

## Your Real_Leads.csv File

### Current Data (Sample)

```csv
name,email,value,location,phone
John Doe,john@example.com,500000,Houston TX,713-555-0123
Jane Smith,jane@example.com,750000,Dallas TX,214-555-0456
Bob Wilson,bob@example.com,600000,Austin TX,512-555-0789
Sarah Johnson,sarah@example.com,950000,San Antonio TX,210-555-1011
Mike Brown,mike@example.com,425000,Fort Worth TX,817-555-1213
Emily Davis,emily@example.com,825000,Corpus Christi TX,361-555-1415
David Martinez,david@example.com,550000,Arlington TX,817-555-1617
Jennifer Lee,jennifer@example.com,1200000,Plano TX,469-555-1819
James Anderson,james@example.com,680000,Garland TX,469-555-2021
Lisa Taylor,lisa@example.com,890000,Irving TX,972-555-2223
```

### To Use Your Own Data

1. Open `real_leads.csv` in Excel or text editor
2. Replace with your actual leads
3. Make sure columns are: name, email, value (at minimum)
4. Save the file
5. Run the ingestion command again

---

## Troubleshooting

### "CSV file not found"
Make sure real_leads.csv is in the c:\dev\valhalla directory

### "Invalid email format"
Email must have @ and . (e.g., john@example.com)
Check for spaces or missing characters

### "Value must be numeric"
Values must be numbers without $ or commas
Change: $500,000
To: 500000

### Nothing happens when I run the command
1. Check that environment is activated (.venv should show in terminal)
2. Check that you're in c:\dev\valhalla directory
3. Try running: `python --version` (should show Python 3.13)
4. Run again with more verbose output

### Script seems stuck
It's probably just waiting for the next cycle (sleeping)
This is normal - it will process again after 30 seconds
Or press Ctrl+C to stop

---

## What to Expect

### With 10 Leads per Cycle, 30-Second Intervals:

**Duration** | **Cycles** | **Leads** | **Time to Complete**
---|---|---|---
Test | 3 | 30 | 2 minutes
Short Run | 10 | 100 | 5 minutes
Medium Run | 30 | 300 | 15 minutes
Long Run | 60 | 600 | 30 minutes
Full Hour | 120 | 1,200 | 60 minutes
Full Day | 2,880 | 28,800 | 24 hours
Full Week | 20,160 | 201,600 | 7 days

---

## Advanced: Custom Configuration

### Change Interval to 60 Seconds

```python
from continuous_ingestion import ContinuousDataIngestion

ing = ContinuousDataIngestion(
    csv_path="real_leads.csv",
    interval=60  # Changed from 30
)
ing.run_continuous()
```

### Use Different CSV File

```python
from continuous_ingestion import ContinuousDataIngestion

ing = ContinuousDataIngestion(
    csv_path="C:\\Users\\YourName\\Documents\\my_leads.csv",
    interval=30
)
ing.run_continuous()
```

### Run in Python File (Not Command Line)

Create `run_ingestion.py`:

```python
from continuous_ingestion import ContinuousDataIngestion

if __name__ == "__main__":
    ing = ContinuousDataIngestion("real_leads.csv", interval=30)
    ing.run_continuous(max_cycles=10)
```

Then run:
```powershell
python run_ingestion.py
```

---

## Key Files

| File | What It Does |
|------|--------------|
| continuous_ingestion.py | Main script - runs the ingestion |
| real_leads.csv | Your lead data - gets ingested each cycle |
| logs/continuous_ingestion_stats.json | Results - statistics saved here |

---

## Quick Reference: Copy & Paste Commands

```powershell
# Navigate to folder
cd c:\dev\valhalla

# Activate environment
.\.venv\Scripts\Activate.ps1

# Run unlimited (press Ctrl+C to stop)
python continuous_ingestion.py

# Run test (3 cycles, ~2 minutes)
python -c "from continuous_ingestion import ContinuousDataIngestion; ContinuousDataIngestion('real_leads.csv', interval=5).run_continuous(max_cycles=3)"

# Run 30 cycles (15 minutes)
python -c "from continuous_ingestion import ContinuousDataIngestion; ContinuousDataIngestion('real_leads.csv').run_continuous(max_cycles=30)"

# View results
type logs\continuous_ingestion_stats.json

# View dashboard (new window)
python show_ops_cockpit.py
```

---

**That's it! Your sandbox is now running continuous real data ingestion.**

Start with the test command (3 cycles) to verify everything works, then run the full production version.

Ctrl+C stops it anytime.

Statistics saved automatically to logs/continuous_ingestion_stats.json.

Good to go! 🚀
