# VALHALLA PRODUCTION MODE - QUICK REFERENCE

## Production Activation Complete ✓

Your Valhalla system is now running in **PRODUCTION MODE** with:
- **Dry-run mode: DISABLED** (real data processing enabled)
- **CSV ingestion: ACTIVE** (10 leads processed)
- **Risk monitoring: OPERATIONAL** (all systems healthy)
- **Real data: FLOWING** (through complete pipeline)

---

## Key Commands

### View Production Workflow
```bash
python production_workflow.py
```
- Disables dry-run
- Ingests CSV data
- Runs risk assessment
- Processes leads

### Run Risk Monitoring
```bash
python risk_monitoring_system.py
```
- Data quality assessment
- System performance check
- Security verification
- Alert summary

### Validate Production Mode
```bash
python validate_production_mode.py
```
- Complete workflow validation
- All checks in one report
- Generates validation summary

### Manage Sandbox Service
```bash
python sandbox_controller.py status    # Check service status
python sandbox_controller.py start     # Start service
python sandbox_controller.py stop      # Stop service
python sandbox_controller.py restart   # Restart service
```

### View Live Dashboard
```bash
python show_ops_cockpit.py
```
- Real-time metrics
- System status
- Processing stats

---

## CSV Data Format

Your test data (`real_leads.csv`) contains:
```
name,email,value,location,phone
John Doe,john.doe@realestate.com,500000,Houston TX,713-555-0123
Jane Smith,jane.smith@homes.com,750000,Dallas TX,214-555-0456
[8 more leads...]
```

**Add more leads:** Follow this format with your own data.

---

## Risk Monitoring System

### Three-Tier Monitoring

1. **Data Quality**
   - Validates every record
   - Checks for duplicates
   - Ensures completeness
   - Threshold: 85% quality score minimum

2. **System Performance**
   - CPU monitoring (limit: 80%)
   - Memory tracking (limit: 80%)
   - Database connections (max: 10)
   - Request latency (max: 30s)

3. **Security**
   - Encryption verification
   - Access control checks
   - Audit logging
   - Threat detection

### Alert Levels
- **CRITICAL:** Halts processing, immediate action needed
- **WARNING:** Degraded operation, review recommended
- **INFO:** Monitoring message, informational only

---

## Current System Status

| Metric | Status | Value |
|--------|--------|-------|
| Mode | PRODUCTION | Enabled |
| Dry-Run | DISABLED | Off |
| Real Data | ENABLED | Active |
| Leads Ingested | COMPLETE | 10/10 |
| Data Quality | HEALTHY | 95.0% |
| CPU Usage | NORMAL | 2.3% |
| Memory Usage | NORMAL | 13.27 MB |
| Risk Level | LOW | Healthy |
| Alerts | NONE | 0 Critical |

---

## Log Files

All production data is logged to:

```
logs/
├── production_execution.json        (Production workflow results)
├── risk_monitoring_results.json     (Risk assessment details)
└── production_validation_complete.json (Validation report)
```

---

## Monitoring Configuration

### Data Quality Thresholds
- Minimum quality score: 85%
- Duplicate tolerance: 0
- Missing fields allowed: 2 max

### System Performance Thresholds
- CPU limit: 80%
- Memory limit: 80%
- DB connections: 10 max
- Request timeout: 30 seconds

### Security Requirements
- Encryption: ENABLED
- Audit logging: ACTIVE
- Access control: CONFIGURED

---

## Real Data Processing Pipeline

Each lead goes through 6 pipeline stages:

1. **A/B Test Tracking** - Tracks test group assignment
2. **Script Promotion** - Evaluates lead quality
3. **Deal Packet** - Generates deal information
4. **Outcome Evaluation** - Scores lead potential
5. **Clone Readiness** - Checks readiness for replication
6. **Lead Scoring** - Final quality score

---

## Authentication

Valhalla uses OAuth2 + JWT authentication:
- **Username:** The All father
- **Password:** IAmBatman!1

---

## Emergency Procedures

### Stop All Processing
```bash
python sandbox_controller.py stop
```

### Check System Health
```bash
python risk_monitoring_system.py
```

### View Current Status
```bash
python show_ops_cockpit.py
```

### Re-enable Dry-Run (if needed)
Modify `production_workflow.py` and set:
```python
dry_run_mode = True
```

---

## Support Resources

- **Full documentation:** [PRODUCTION_MODE_COMPLETE.md](PRODUCTION_MODE_COMPLETE.md)
- **Production scripts:** production_workflow.py, risk_monitoring_system.py
- **Service controller:** sandbox_controller.py
- **Dashboard:** show_ops_cockpit.py
- **Test data:** real_leads.csv

---

## Next Steps

1. **Monitor continuously** - Risk monitoring runs all checks
2. **Add your data** - Upload CSV files with your real leads
3. **Review logs** - Check logs/ folder for monitoring data
4. **Adjust thresholds** - Customize risk monitoring limits if needed
5. **Scale up** - Add more leads as system proves stable

---

## Feature Summary

✓ Dry-run disabled (real data processing)
✓ CSV ingestion with validation
✓ Data quality monitoring
✓ System performance tracking
✓ Security verification
✓ Real-time alerting
✓ Production logging
✓ Pipeline processing
✓ Risk assessment
✓ Continuous monitoring

---

**Status:** PRODUCTION READY
**Mode:** Real Data Processing
**Dry-Run:** DISABLED
**Last Updated:** 2026-01-07
