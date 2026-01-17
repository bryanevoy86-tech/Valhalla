# Capital/Metrics/Telemetry Backend Pack - Deployment Guide

**Status:** ✅ Code committed and pushed to main branch  
**Commit:** `5c6dff2` - feat(capital): add capital intake, metrics, telemetry, forecast/freeze jobs  
**Deployment:** Render auto-deploy triggered (watch at https://dashboard.render.com)

---

## 🎯 What Was Added

### Configuration Settings (config.py)
```python
FREEZE_DRAWDOWN_PCT: float = 0.02    # 2% drawdown threshold for freeze checks
FORECAST_MONTHLY_YIELD: float = 0.04  # 4% expected monthly yield for projections
```

### Models (Database Tables)

#### TelemetryEvent (`telemetry_events` table)
Tracks system activity, builds, ingestions, and errors.
- `id`: Integer primary key
- `kind`: String(80) - event type (e.g., "build", "ingest", "error")
- `message`: Text - event description
- `meta_json`: Text - JSON metadata
- `created_at`: DateTime with timezone

#### CapitalIntake (`capital_intake` table)
Tracks incoming funds from various sources.
- `id`: Integer primary key
- `source`: String(120) - source name (e.g., "wholesaling", "fx", "flip")
- `currency`: String(12) - default "CAD"
- `amount`: Numeric(18,2) - monetary amount
- `note`: String(280) - optional notes
- `created_at`: DateTime with timezone

### Schemas (Pydantic Validation)

**TelemetryIn:** Input schema for logging events
- `kind`: str (required)
- `message`: str (optional)
- `meta_json`: str (optional)

**CapitalIn:** Input schema for capital intake
- `source`: str (max 120 chars, required)
- `currency`: str (default "CAD", max 12 chars)
- `amount`: float (required)
- `note`: str (optional)

**CapitalOut:** Output schema with database ID (extends CapitalIn)

### API Endpoints

#### GET /api/metrics
Public endpoint that aggregates counts from all tables.

**Response:**
```json
{
  "ok": true,
  "research_sources": 0,
  "research_docs": 0,
  "telemetry_events": 0,
  "capital_intake_records": 0,
  "builder_tasks": 0,
  "playbooks": 0
}
```

#### POST /api/telemetry
Log a telemetry event. **Requires X-API-Key authentication.**

**Request:**
```json
{
  "kind": "build",
  "message": "Heimdall auto-builder completed task #42",
  "meta_json": "{\"task_id\": 42, \"files\": 5}"
}
```

**Response (201 Created):**
```json
{
  "ok": true,
  "id": 1,
  "kind": "build",
  "created_at": "2025-01-12T10:30:00Z"
}
```

#### POST /api/capital/intake
Record a new capital intake. **Requires X-API-Key authentication.**

**Request:**
```json
{
  "source": "wholesaling",
  "currency": "CAD",
  "amount": 15000.00,
  "note": "Deal #42 closed"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "source": "wholesaling",
  "currency": "CAD",
  "amount": 15000.00,
  "note": "Deal #42 closed",
  "created_at": "2025-01-12T10:30:00Z"
}
```

#### GET /api/capital/intake?limit=200
List recent capital intake records. **Requires X-API-Key authentication.**

**Response:**
```json
[
  {
    "id": 5,
    "source": "fx_trading",
    "currency": "CAD",
    "amount": 2500.00,
    "note": "EUR/CAD position closed",
    "created_at": "2025-01-12T10:30:00Z"
  },
  ...
]
```

#### GET /api/jobs/forecast/month
Calculate projected balance one month ahead. **Requires X-API-Key authentication.**

**Formula:** `total_capital * (1 + FORECAST_MONTHLY_YIELD)`

**Response:**
```json
{
  "ok": true,
  "current_total": 50000.00,
  "forecast_yield": 0.04,
  "projected_balance": 52000.00,
  "currency": "CAD",
  "note": "Projected balance one month ahead with 4% yield"
}
```

#### GET /api/jobs/freeze/check?prev_balance=50000&current_balance=49000
Check if drawdown exceeds freeze threshold. **Requires X-API-Key authentication.**

**Formula:** `(prev_balance - current_balance) / prev_balance >= FREEZE_DRAWDOWN_PCT`

**Response (within threshold):**
```json
{
  "ok": true,
  "frozen": false,
  "drawdown_pct": 0.02,
  "threshold_pct": 0.02,
  "prev_balance": 50000.00,
  "current_balance": 49000.00,
  "message": "Within acceptable drawdown"
}
```

**Response (freeze triggered):**
```json
{
  "ok": true,
  "frozen": true,
  "drawdown_pct": 0.03,
  "threshold_pct": 0.02,
  "prev_balance": 50000.00,
  "current_balance": 48500.00,
  "message": "FREEZE TRIGGERED - 3.00% drawdown"
}
```

### Jobs (Business Logic)

**forecast_jobs.py:**
- `forecast_month_ahead(db)` - Calculates projected balance based on forecast yield
- Queries total capital from `capital_intake` table
- Applies `FORECAST_MONTHLY_YIELD` multiplier

**freeze_jobs.py:**
- `check_drawdown(prev_balance, current_balance)` - Risk management alert system
- Compares current balance to previous balance
- Returns freeze flag if drawdown exceeds `FREEZE_DRAWDOWN_PCT` threshold

### Migration

**20251102_v3_4_capital_telemetry.py**
- Creates `telemetry_events` table with indexes on `kind` and `created_at`
- Creates `capital_intake` table with indexes on `source` and `created_at`
- Down-revision: `v3_4_embeddings`

### Testing

**test_metrics_capital.py**
- `test_metrics_ok()` - Validates /metrics endpoint structure
- `test_capital_roundtrip()` - Creates capital intake, lists records, verifies presence
- `test_telemetry_create()` - Logs telemetry event and validates response

### Auto-Builder Enhancements

**tools/auto_build.py** now supports multi-file packs:
- `pack_metrics_capital()` - Reads and returns all capital/metrics/telemetry files
- `pack_tests()` - Returns test files
- `draft_apply(title, files, dry_run)` - Helper for task creation and application
- CLI interface: `python tools/auto_build.py metrics_capital`

---

## 🚀 Deployment Steps

### 1. Wait for Render Auto-Deploy
Check deployment status at: https://dashboard.render.com

The push to `main` branch automatically triggers Render deployment.

### 2. Run Database Migration
Once deployment completes, run the migration to create new tables:

**Option A: Via Admin API**
```bash
curl -X POST https://valhalla-api-ha6a.onrender.com/api/admin/migrate \
  -H "X-Admin-Key: YOUR_ADMIN_KEY"
```

**Option B: Via Render Shell**
```bash
# In Render dashboard -> Shell
cd services/api
alembic upgrade head
```

### 3. Verify Deployment
```bash
# Check API is responding
curl https://valhalla-api-ha6a.onrender.com/healthz

# Check metrics endpoint
curl https://valhalla-api-ha6a.onrender.com/api/metrics

# Should see capital_intake_records and telemetry_events fields
```

### 4. Test Capital Intake
```bash
# Create a capital intake record
curl -X POST https://valhalla-api-ha6a.onrender.com/api/capital/intake \
  -H "X-API-Key: YOUR_BUILDER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test_deployment",
    "currency": "CAD",
    "amount": 1000.00,
    "note": "Deployment verification test"
  }'

# List capital intake records
curl https://valhalla-api-ha6a.onrender.com/api/capital/intake \
  -H "X-API-Key: YOUR_BUILDER_KEY"
```

### 5. Test Telemetry
```bash
curl -X POST https://valhalla-api-ha6a.onrender.com/api/telemetry \
  -H "X-API-Key: YOUR_BUILDER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "deployment",
    "message": "Capital/metrics pack deployed successfully",
    "meta_json": "{\"version\": \"3.4\"}"
  }'
```

### 6. Test Forecast and Freeze Jobs
```bash
# Test forecast
curl "https://valhalla-api-ha6a.onrender.com/api/jobs/forecast/month" \
  -H "X-API-Key: YOUR_BUILDER_KEY"

# Test freeze check (within threshold)
curl "https://valhalla-api-ha6a.onrender.com/api/jobs/freeze/check?prev_balance=50000&current_balance=49000" \
  -H "X-API-Key: YOUR_BUILDER_KEY"

# Test freeze check (exceeds threshold)
curl "https://valhalla-api-ha6a.onrender.com/api/jobs/freeze/check?prev_balance=50000&current_balance=48000" \
  -H "X-API-Key: YOUR_BUILDER_KEY"
```

### 7. Run Test Suite
```bash
# Locally
cd services/api
pytest tests/test_metrics_capital.py -v

# Against Render
API_BASE=https://valhalla-api-ha6a.onrender.com \
HEIMDALL_BUILDER_API_KEY=YOUR_KEY \
pytest tests/test_metrics_capital.py -v
```

---

## 📊 Expected Migration Output

When you run `alembic upgrade head`, you should see:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade v3_4_embeddings -> v3_4_capital_telemetry, create telemetry and capital tables
```

Verify tables exist:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('telemetry_events', 'capital_intake');
```

---

## 🔧 Troubleshooting

### Migration Fails
If migration fails, check:
1. Previous migration `v3_4_embeddings` was applied successfully
2. Database credentials are correct in `.env` or Render environment variables
3. PostgreSQL version compatibility (should be 13+)

**Fix:**
```bash
# Check current revision
alembic current

# If stuck, manually set revision (use with caution)
alembic stamp v3_4_embeddings
alembic upgrade head
```

### Import Errors
If new routers fail to import, check:
1. Migration was run successfully (tables must exist for models to import)
2. No circular dependencies in imports
3. All required packages in `requirements.txt` are installed

**Fix:**
```bash
# Restart Render service after migration
# Dashboard -> Manual Deploy -> Clear build cache
```

### Authentication Issues
If endpoints return 401 Unauthorized:
1. Verify `X-API-Key` header is set correctly
2. Check `HEIMDALL_BUILDER_API_KEY` environment variable on Render
3. Confirm `require_builder_key` dependency is imported correctly

**Fix:**
```bash
# Test with correct key format
curl -H "X-API-Key: your-actual-key" https://...
```

---

## 🎉 Success Indicators

You'll know deployment succeeded when:

✅ `/api/metrics` returns counts for `capital_intake_records` and `telemetry_events`  
✅ POST to `/api/capital/intake` creates record and returns ID  
✅ GET to `/api/capital/intake` lists created records  
✅ POST to `/api/telemetry` logs events successfully  
✅ GET to `/api/jobs/forecast/month` calculates projection  
✅ GET to `/api/jobs/freeze/check` evaluates drawdown thresholds  
✅ All tests in `test_metrics_capital.py` pass  
✅ GitHub Actions CI/CD pipeline passes (coverage ≥95%, mypy passes)

---

## 📈 Next Steps

### Immediate
1. Run migration on Render
2. Test all new endpoints manually
3. Run pytest suite to verify integration
4. Monitor metrics endpoint for data accumulation

### Future Enhancements
1. **Scheduled Jobs:** Add GitHub Actions workflow to call forecast/freeze jobs nightly
2. **Alerting:** Create webhook integration to notify on freeze triggers
3. **Dashboard:** Build frontend visualization for capital intake and metrics
4. **Historical Analysis:** Add endpoints for trend analysis and performance metrics
5. **Multi-Currency:** Enhance to support automatic currency conversion
6. **Risk Profiles:** Add configurable risk thresholds per capital source

### Auto-Builder Integration
The enhanced `auto_build.py` can now handle large multi-file packs:

```bash
# Build reports feature
python tools/auto_build.py reports

# Build capital/metrics pack
python tools/auto_build.py metrics_capital
```

This enables Heimdall to autonomously apply complex feature packs using the Builder API.

---

## 📚 Related Documentation

- **HEIMDALL_SEMANTIC_WORKFLOW.md** - Semantic search implementation
- **AUTO_BUILDER_GUIDE.md** - Comprehensive auto-builder documentation
- **README.md** - Main project documentation
- **Alembic migrations/** - Database schema evolution history

---

**Deployed:** 2025-01-12  
**Version:** 3.4  
**Author:** Heimdall AI Builder  
**Repository:** github.com/bryanevoy86-tech/Valhalla
