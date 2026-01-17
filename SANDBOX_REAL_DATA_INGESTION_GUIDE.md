# SANDBOX REAL DATA INGESTION - COMPLETE SETUP GUIDE

## Overview

Your sandbox is now configured to run **continuous real data ingestion** from CSV files. The system will continuously ingest, validate, and process leads while monitoring for risks.

---

## Step 1: Environment Verification

Your environment is already set up:

✓ Python virtual environment: Active
✓ Sandbox service: Running (persistent mode)
✓ CSV ingestion module: Ready
✓ Risk monitoring: Active

---

## Step 2: Prepare Your CSV File

### Required Format

Your CSV must have these columns:

```csv
name,email,value,location,phone
John Doe,john@example.com,500000,Houston TX,713-555-0123
Jane Smith,jane@example.com,750000,Dallas TX,214-555-0456
```

### Required Fields
- **name:** Lead name (text)
- **email:** Email address (must have @ and .)
- **value:** Lead value (positive number)

### Optional Fields
- **location:** City/state
- **phone:** Phone number
- **source:** Data source identifier

---

## Step 3: Run Continuous Ingestion

### Option A: Interactive Continuous Ingestion (Runs Forever)

```bash
# Activate environment (if not already active)
.\.venv\Scripts\Activate.ps1

# Run continuous ingestion - stops when you press Ctrl+C
python continuous_ingestion.py
```

This will:
- Read real_leads.csv every 30 seconds
- Validate each lead
- Process through 6-step pipeline
- Log all activities
- Monitor system health
- Show real-time statistics

### Option B: Test Run (Limited Cycles)

```python
from continuous_ingestion import ContinuousDataIngestion

ingestion = ContinuousDataIngestion("real_leads.csv", interval=30)
ingestion.run_continuous(max_cycles=10)  # Run 10 cycles then stop
```

### Option C: Sandbox Integration (Setup Once)

```bash
python sandbox_real_data_integration.py
```

This sets up and runs continuous ingestion integrated with your sandbox.

---

## Step 4: Update CSV File Path (Optional)

If your CSV is not in the valhalla directory, update the path in `continuous_ingestion.py`:

```python
# Line in main():
csv_path = Path(__file__).parent / "real_leads.csv"

# Change to your path:
csv_path = Path("C:/Users/YourName/Documents/my_leads.csv")
```

Or pass it as an argument:

```python
ingestion = ContinuousDataIngestion(
    csv_path="C:\\path\\to\\your\\file.csv",
    interval=30
)
ingestion.run_continuous()
```

---

## What Happens During Continuous Ingestion

### Each Cycle (Default: Every 30 Seconds)

1. **Read CSV File**
   - Opens your CSV file
   - Reads all records

2. **Validate Data**
   - Checks required fields (name, email, value)
   - Validates email format
   - Verifies numeric values
   - Reports invalid records

3. **Sanitize Data**
   - Trims whitespace
   - Converts emails to lowercase
   - Standardizes values
   - Adds timestamps

4. **Process Through Pipeline**
   - A/B Test Tracking
   - Script Promotion
   - Deal Packet Generation
   - Outcome Evaluation
   - Clone Readiness
   - Lead Scoring

5. **Run Risk Assessment**
   - Data quality score
   - System performance check
   - Security verification
   - Generate alerts

6. **Log Results**
   - Save statistics
   - Update JSON reports
   - Display console output

---

## Monitoring During Ingestion

### Console Output

You'll see real-time output:

```
[2026-01-07 19:12:28] [CYCLE 1] Starting ingestion cycle...
[PROCESSING] John Doe - john@example.com - Value: $500,000.00
  [1/6] A/B Test Tracking: PROCESSED
  [2/6] Script Promotion: PROCESSED
  ...
[2026-01-07 19:12:28] [OK] Cycle 1 complete: 10 leads ingested
  Statistics:
    Cycles completed: 1
    Total leads ingested: 10
    Valid leads: 10
    Uptime: 0h 0m 0s
```

### JSON Reports

Check these files for detailed results:

- **logs/continuous_ingestion_stats.json** - Ingestion statistics
- **logs/production_execution.json** - Production data
- **logs/risk_monitoring_results.json** - Risk assessment
- **logs/production_validation_complete.json** - Validation report

### Live Dashboard

While ingestion is running, in another terminal:

```bash
python show_ops_cockpit.py
```

---

## Continuous Ingestion Behavior

### Default Configuration

```python
# Interval: 30 seconds between cycles
# Cycles: Unlimited (runs until stopped)
# Dry-run: ENABLED (protected sandbox)
# Monitoring: ACTIVE
```

### Customization

```python
# Change interval to 60 seconds:
ingestion = ContinuousDataIngestion("file.csv", interval=60)

# Run specific number of cycles:
ingestion.run_continuous(max_cycles=100)

# Stop with Ctrl+C
```

---

## Error Handling

### Missing CSV File
```
[ERROR] CSV file not found: /path/to/file.csv
```
**Solution:** Check file path exists and is accessible

### Invalid Email Format
```
[ERROR] Invalid email format: john.example.com
```
**Solution:** Email must contain @ and . (e.g., john@example.com)

### Non-Numeric Value
```
[ERROR] Value must be numeric: abc
```
**Solution:** Value must be a number (e.g., 500000)

---

## Statistics Tracking

The system tracks:

- **Cycles completed:** Number of ingestion cycles
- **Total leads ingested:** Sum of all leads processed
- **Valid leads:** Successfully validated leads
- **Invalid leads:** Failed validation
- **Average leads/cycle:** Mean per cycle
- **Uptime:** Total running time
- **Status:** Current state (RUNNING, STOPPED, etc.)

Example output:
```
Total Cycles: 10
Total Leads Ingested: 100
Valid Leads: 100
Invalid Leads: 0
Average Leads/Cycle: 10.0
Total Uptime: 305.2s
Status: RUNNING
```

---

## System Interaction

### Sandbox Status

Your sandbox continues running alongside continuous ingestion:
- Sandbox: Processing test leads (dry-run mode)
- Ingestion: Processing real data (configurable)
- Both: Monitored by risk management system

### Risk Monitoring

Real-time monitoring includes:

- **Data Quality:** Validates ingested data
- **System Performance:** CPU, memory, connections
- **Security:** Encryption, access control, audit logging

Alert levels:
- CRITICAL: Stop processing
- WARNING: Action recommended
- INFO: Informational message

---

## Example Workflows

### Workflow 1: Single Test Run

```bash
python -c "
from continuous_ingestion import ContinuousDataIngestion
ing = ContinuousDataIngestion('real_leads.csv', interval=5)
ing.run_continuous(max_cycles=3)
"
```

### Workflow 2: Continuous Production

```bash
python continuous_ingestion.py
# Press Ctrl+C to stop
```

### Workflow 3: Custom Interval

```python
from continuous_ingestion import ContinuousDataIngestion

ing = ContinuousDataIngestion(
    csv_path="my_leads.csv",
    interval=60  # Ingest every 60 seconds
)
ing.run_continuous()  # Unlimited cycles
```

### Workflow 4: Scheduled Processing

```python
from continuous_ingestion import ContinuousDataIngestion

ing = ContinuousDataIngestion("leads.csv", interval=1800)  # Every 30 min
ing.run_continuous(max_cycles=48)  # 24 hours of data
```

---

## Best Practices

1. **Test First**
   - Run with max_cycles=3 to test configuration
   - Check logs for any errors
   - Verify data is valid

2. **Monitor Performance**
   - Watch CPU and memory usage
   - Check risk alerts in real-time
   - Review logs regularly

3. **Data Validation**
   - Ensure CSV format is correct
   - Test with sample data first
   - Validate field formats

4. **Backup Data**
   - Keep backup of original CSV
   - Save ingestion reports
   - Archive logs periodically

5. **Graceful Shutdown**
   - Use Ctrl+C to stop ingestion
   - Final report will be generated
   - Statistics saved to JSON

---

## File Reference

### New Files Created

- [continuous_ingestion.py](continuous_ingestion.py) - Main ingestion module
- [sandbox_real_data_integration.py](sandbox_real_data_integration.py) - Sandbox integration
- [test_continuous.py](test_continuous.py) - Test script (auto-generated)

### Key Modules

- csv_ingestion.py - CSV reader and validator
- risk_monitoring_system.py - Risk assessment
- sandbox_controller.py - Service management

### Output Files

- logs/continuous_ingestion_stats.json - Statistics
- logs/production_execution.json - Production data
- logs/risk_monitoring_results.json - Risk assessment

---

## Troubleshooting

### Script stops unexpectedly
Check logs/ folder for error messages

### Memory usage increasing
Check for infinite loops in data processing
Consider running fewer cycles at a time

### CSV not updating
Ensure file permissions allow read access
Check file path is correct
Verify CSV format is valid

### Risk alerts appearing
Review alert in logs/
Adjust thresholds in risk_monitoring_system.py
Check system resources (CPU, memory)

---

## Next Steps

1. **Prepare your CSV file** with required columns
2. **Place in valhalla directory** or update path
3. **Test with limited cycles** (max_cycles=3)
4. **Review logs** for any issues
5. **Run continuous ingestion** (remove max_cycles)
6. **Monitor with dashboard** (python show_ops_cockpit.py)

---

## Commands Quick Reference

```bash
# Run continuous ingestion (unlimited)
python continuous_ingestion.py

# Setup and run with sandbox integration
python sandbox_real_data_integration.py

# View real-time dashboard
python show_ops_cockpit.py

# Check sandbox status
python sandbox_controller.py status

# View risk assessment
python risk_monitoring_system.py

# Check ingestion statistics
cat logs/continuous_ingestion_stats.json
```

---

**Status:** READY FOR PRODUCTION
**Last Updated:** 2026-01-07
**System:** Sandbox + Continuous Real Data Ingestion

Your sandbox is now set up for continuous real data ingestion!
