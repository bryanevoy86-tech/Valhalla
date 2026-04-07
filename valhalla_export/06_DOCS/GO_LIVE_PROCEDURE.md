# VALHALLA GO-LIVE PROCEDURE

## Status: ✅ CLEARED FOR PRODUCTION

Generated: 2026-01-25 20:32:07 UTC

### Prerequisites Met
- ✅ Backend health: **PASS**
- ✅ All 16 packs installed: **PASS**
- ✅ Kill-switch: **Disengaged**
- ✅ Risk policies: **4 active**
- ✅ Regression tripwires: **4 active**
- ✅ Heimdall charter policies: **Present**

---

## STEP 1: Enable Go-Live Mode

Enable production execution on your API:

```bash
cd c:\dev\valhalla
python go_live.py --base https://valhalla-api-ha6a.onrender.com --csv <your_data_file.csv>
```

### Example: Ingest Your First Data Batch

```bash
# Find available data files:
ls PHASE_*.csv

# Run with first batch:
python go_live.py --csv PHASE_1_metrics_20260107_231516.csv
```

---

## STEP 2: Monitor Live Execution

Once go-live is enabled, monitor real-time status:

```bash
# Single status check
python ops_report.py

# Continuous monitoring (every 60 seconds)
python ops_report.py --watch 60
```

The output will show:
- **Next actions**: What to do operationally
- **Health**: Backend status
- **Governance**: Blockers, warnings, OK status

---

## STEP 3: Operational Workflow

After go-live:

1. **Intake**: Leads flow into the system
2. **Scripts & Packages**: Execution via packs
3. **A/B Testing**: Tracking variant performance
4. **Deal Packets**: Auto-generated for promising leads
5. **Regression Monitoring**: Tripwires monitor for quality drop
6. **Clone Readiness**: Top performers queued for scaling

---

## Key Commands

### Data Ingestion
```bash
# Enable go-live + ingest data
python go_live.py --csv <file.csv>

# Ingest additional data batch (go-live already enabled)
python go_live.py --csv <file.csv> --no-enable
```

### Monitoring
```bash
# One-time status check
python ops_report.py

# Live dashboard (updates every 60 seconds)
python ops_report.py --watch 60

# View last status report
cat ops_out/ops_status.md
cat ops_out/ops_status.json
```

### Risk Management
```bash
# Check all active policies (risk floors/caps, regressions, etc)
# Via governance endpoint:
curl https://valhalla-api-ha6a.onrender.com/api/governance/runbook/status
```

---

## What Happens at Go-Live

1. **Kill-switch disengaged** → System accepts live data
2. **All packs activated** → 16 execution pipelines running
3. **Risk policies enforced** → Floors, caps, approval workflows active
4. **Regression monitoring** → Tripwires alert on quality drop
5. **Heimdall governance** → Policy compliance checked continuously
6. **Data flow** → Leads → Scripts → Packets → Outcomes

---

## Rollback / Safety

If issues occur:

1. Check governance blockers:
   ```bash
   python ops_report.py
   ```

2. Engage kill-switch (if needed):
   ```bash
   curl -X POST https://valhalla-api-ha6a.onrender.com/api/governance/kill-switch/engage
   ```

3. Review risk policies and thresholds
4. Contact ops team

---

## Success Criteria

- Lead intake flowing into system
- Scripts executing on schedule
- Deal packets generating
- No regression tripwire alerts
- Governance blockers = 0
- Health endpoint = 200 OK

---

**Ready?** Run:
```bash
python go_live.py --csv <your_data.csv>
```

Then monitor:
```bash
python ops_report.py --watch 60
```
