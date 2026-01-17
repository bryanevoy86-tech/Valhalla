# PACK L, M, N Quick Reference

## Three Critical Systems

### PACK L — Canon (SSOT)
**What:** Single source of truth for engines, classes, bands  
**Endpoint:** `GET /core/canon`  
**Returns:** Authoritative system configuration  
**Key Fields:** canon_version, band_policy, engine_registry, locked_engines

### PACK M — Reality (Audits)
**What:** Weekly state snapshots for compliance  
**Endpoints:**
- `POST /core/reality/weekly_audit` → Record state
- `GET /core/reality/weekly_audits?limit=20` → List audits

**Returns:** Audit records with cone, lite, session, next_step  
**Storage:** `data/weekly_audits.json` (500 max, newest first)

### PACK N — Export (Bundle)
**What:** Downloadable ZIP of state files  
**Endpoint:** `GET /core/export/bundle`  
**Returns:** ZIP file (`valhalla_export_YYYYMMDD_HHMMSS.zip`)  
**Contents:** cone_state.json, leads.json, audit_log.json, etc.

---

## Usage

### Get Canon (SSOT)
```bash
curl http://localhost:4000/core/canon | jq .
```
See: band_policy, engine_registry, locked_engines

### Record Weekly Audit
```bash
curl -X POST http://localhost:4000/core/reality/weekly_audit | jq .
```
Creates snapshot: cone + lite + session + next

### List Past Audits
```bash
curl http://localhost:4000/core/reality/weekly_audits?limit=5 | jq .
```
Returns: 5 newest audits, newest first

### Download State Bundle
```bash
curl -OJ http://localhost:4000/core/export/bundle
```
Downloads: valhalla_export_*.zip

---

## Files Created

### PACK L (Canon)
```
backend/app/core_gov/canon/
├── __init__.py         (docstring)
├── service.py          (canon_snapshot fn)
└── router.py           (GET /canon endpoint)
```

### PACK M (Reality)
```
backend/app/core_gov/reality/
├── __init__.py         (docstring)
├── weekly_store.py     (load/append audits)
├── weekly_service.py   (run_weekly_audit fn)
└── router.py           (POST/GET endpoints)
```

### PACK N (Export)
```
backend/app/core_gov/export/
├── __init__.py         (docstring)
├── service.py          (build_export_bundle fn)
└── router.py           (GET /bundle endpoint)
```

### Integration
```
backend/app/core_gov/
└── core_router.py      (+6 lines: 3 imports, 3 includes)
```

---

## Test Command

Verify all three are working:

```bash
curl http://localhost:4000/core/canon
curl -X POST http://localhost:4000/core/reality/weekly_audit
curl http://localhost:4000/core/reality/weekly_audits?limit=1
curl -O http://localhost:4000/core/export/bundle
```

---

## Data Examples

### Canon Response
```json
{
  "canon_version": "1.0.0",
  "locked_model": "UA-1 Full Authority Aggressive (but Safe)",
  "boring_engines_locked": ["storage", "cleaning", "landscaping"],
  "band_policy": {
    "A": {"intent": "Expansion / Normal", ...},
    "B": {"intent": "Caution", ...},
    "C": {"intent": "Stabilization", ...},
    "D": {"intent": "Survival", ...}
  },
  "engine_registry": {...},
  "thresholds": {...},
  "capital_usage": {...}
}
```

### Audit Record
```json
{
  "created_at_utc": "2026-01-01T10:00:00Z",
  "cone": {"band": "B", "reason": "...", "updated_at_utc": "..."},
  "lite": {"status": "green"},
  "go_session": {"active": true, "status": "running"},
  "next": {"step_num": 5, "title": "Next action"}
}
```

---

## Common Patterns

### Weekly Cadence
```bash
# Monday AM
curl -X POST http://localhost:4000/core/reality/weekly_audit

# Friday PM
curl http://localhost:4000/core/reality/weekly_audits?limit=7 | jq .
```

### Check State at Point in Time
```bash
# Get all audits
curl http://localhost:4000/core/reality/weekly_audits?limit=500 | jq '.items[] | select(.created_at_utc == "2026-01-01T...")'
```

### Export for Audit
```bash
# Download state
curl -OJ http://localhost:4000/core/export/bundle

# Unzip
unzip valhalla_export_*.zip

# Review files
cat leads.json | jq .
cat audit_log.json | jq .
```

---

## Integration Points

### PACK L (Canon)
- Used by: UI, operators, auditors
- Reads from: cone, config, capital modules
- Returns: Single JSON object (SSOT)

### PACK M (Reality)
- Called by: Operators, scheduled jobs
- Reads from: cone, health, go, audit
- Writes to: data/weekly_audits.json
- Logs: WEEKLY_AUDIT_RUN event

### PACK N (Export)
- Called by: Auditors, operators, support
- Reads from: data/*.json files
- Returns: ZIP file
- Logs: EXPORT_BUNDLE_CREATED event

---

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| GET /core/canon | <100ms | Reads config + registry |
| POST /weekly_audit | <200ms | Records + logs |
| GET /weekly_audits (20 items) | <50ms | Reads file |
| GET /export/bundle | <500ms | Creates ZIP |

---

## Capacity

| System | Capacity | Notes |
|--------|----------|-------|
| Weekly Audits | 500 records | Auto-caps, keeps newest |
| Export Bundle | All files | Includes available data files |
| Canon | No limit | Single snapshot at a time |

---

*PACK L, M, N Quick Reference*  
*Production Ready ✅*
