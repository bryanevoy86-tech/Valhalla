## Deal Schema Mismatch: lead_id vs ext_id Fix

**Date:** 2026-03-31 03:32 UTC  
**Issue:** GET /api/deals endpoint failing with `column deals.lead_id does not exist`  
**Root Cause:** Schema mismatch between pack_62_underwriter production deals table and ORM expectations

---

## Root Cause Analysis

### The Problem

Two incompatible schema definitions were using the same "deals" table name:

| Aspect | pack_62_underwriter (Production) | ORM/API Expected | Status |
|--------|------|------|--------|
| **Created By** | Underwriter engine migration | Lead-to-deal pipeline ORM | |
| **Table Columns** | id, ext_id, address, city, lat, lng, status, ask_price, notes, meta | id, lead_id, title, stage, arv, estimated_repair_cost, max_allowable_offer, score, etc. | ❌ Total mismatch |
| **Purpose** | Underwrite real estate deals (geolocation focus) | Manage lead-to-deal lifecycle (pipeline focus) | |
| **Foreign Keys** | No lead FK | lead_id→leads.id | |
| **Leading Issue** | Has ext_id (String, external ID) | Needs lead_id (Integer FK) | ❌ Column missing |

### Timeline of Errors

1. **Earlier:** `column deals.updated_ts does not exist` → Fixed with migration 20260330_add_updated_ts_to_deals
2. **Current:** `column deals.lead_id does not exist` → Root cause: entire schema incompatibility

### Why This Happened

- pack_62 migration created the deals table first (for underwriting functionality)
- Later pipeline ORM expected a different deals table schema
- No migration existed to bridge the schemas - they were left incompatible
- ORM query tries to SELECT columns that don't exist in production table

---

## Solution: Schema Bridge Migrations

Instead of recreating the table (data-destroying), we add missing columns incrementally.

### Source of Truth Decision

**Production pack_62 deals table IS the authoritative source.**
- It exists in production
- Related features depend on it (comps table, underwriting_signals, deal_scores FK to deals.id)
- Replacing it would destroy historical data
- **Solution:** Add missing pipeline columns to existing table

### Migrations Created

#### 1. **`20260330_add_updated_ts_to_deals.py`** (Already deployed)
- **Purpose:** Add missing `updated_ts` column
- **Status:** ✅ Deployed and executed
- **Changes:** Adds DateTime column with server default

#### 2. **`20260330_add_lead_id_to_deals.py`** (New)
- **Purpose:** Add missing `lead_id` column (INTEGER FK)
- **Status:** Deployed, awaiting Render execution
- **Changes:** Adds Integer column (nullable) with index
- **Dependency:** after add_updated_ts_to_deals
- **File:** `services/api/alembic/versions/20260330_add_lead_id_to_deals.py`

```python
revision = "add_lead_id_to_deals"
down_revision = "add_updated_ts_to_deals"

# Adds: lead_id INTEGER NULL INDEX
```

#### 3. **`20260330_add_deal_pipeline_columns.py`** (New) 
- **Purpose:** Add all remaining ORM-expected columns
- **Status:** Deployed, awaiting Render execution
- **Changes:** Adds 8 columns with sensible defaults
- **Dependency:** after add_lead_id_to_deals
- **File:** `services/api/alembic/versions/20260330_add_deal_pipeline_columns.py`

```python
revision = "add_deal_pipeline_columns"
down_revision = "add_lead_id_to_deals"

# Adds:
# - title VARCHAR(255) DEFAULT 'imported'
# - stage VARCHAR(50) DEFAULT 'lead_received'
# - arv NUMERIC(15,2) NULL
# - estimated_repair_cost NUMERIC(15,2) NULL
# - max_allowable_offer NUMERIC(15,2) NULL
# - target_assignment_fee NUMERIC(15,2) NULL
# - score NUMERIC(8,2) NULL
# - disposition_status VARCHAR(50) NULL
```

---

## Other Code Changes

### 1. **Fixed intake/models.py Double-Mapping** 
**File:** `services/api/app/intake/models.py`

**Problem:** intake/models.py Deal class was also mapping to "deals" table with different columns, causing SQLAlchemy to merge conflicting definitions.

**Solution:**
- Renamed Deal → DealIntakeRecord
- Changed __tablename__ to "deal_intake_records" (separate table)
- Provided backward-compatible alias: `Deal = DealIntakeRecord`

**Result:** intake model no longer conflicts with main deals pipeline

### 2. **Fixed Base Import**
**File:** `services/api/app/intake/models.py`

**Problem:** intake/models.py was creating its own `declarative_base()` which conflicted with main app.core.db.Base

**Solution:** Changed to import Base from app.core.db

**Result:** All ORM models now use same Base instance

---

## Migration Chain

```
20260205_final_consolidation (existing head)
    ↓
20260330_add_updated_ts_to_deals ✅ (already executed)
    ↓
20260330_add_lead_id_to_deals (new - pending)
    ↓
20260330_add_deal_pipeline_columns (new - pending)
```

**Alembic Status:** Linear chain, single head = ✅ verified with `alembic heads`

---

## Expected Outcomes After Deployment

### Phase 1: After add_lead_id migration runs
- Error changes from: `column deals.lead_id does not exist`
- To: `column deals.title does not exist` (next missing column)
- GET /api/deals still returns 500

### Phase 2: After add_deal_pipeline_columns migration runs
- All required columns exist in production table
- ORM can generate complete SQL query
- Columns have sensible defaults for existing rows (backward compatible)
- GET /api/deals returns 200 with list of deals (empty if table is empty)

---

## Verification Checklist

### Before Fix Deployment
```
✅ GET /health: 200 OK
❌ GET /api/deals: 500 (column deals.lead_id does not exist)
```

### After Migration 1 (add_lead_id)
```
✅ GET /health: 200 OK
❌ GET /api/deals: 500 (column deals.title does not exist)
   - Indicates migration ran successfully
   - lead_id column now exists
```

### After Migration 2 (add_deal_pipeline_columns)
```
✅ GET /health: 200 OK
✅ GET /api/deals: 200 (returns [] or deal records)
   - Schema complete
   - ORM query executes successfully
   - Ready for WeWeb integration
```

### Success Criteria
- [ ] GET /api/deals returns HTTP 200
- [ ] Response body is valid JSON list or array
- [ ] Response includes `lead_id` field (even if null)
- [ ] No more `UndefinedColumn` errors in logs

---

## Files Modified

```
services/api/alembic/versions/20260330_add_updated_ts_to_deals.py
    ↓ Already deployed
services/api/alembic/versions/20260330_add_lead_id_to_deals.py
    ↓ New - Deployed, pending execution
services/api/alembic/versions/20260330_add_deal_pipeline_columns.py
    ↓ New - Deployed, pending execution
services/api/app/intake/models.py
    ↓ Fixed double-mapping issue
    ↓ Uses shared Base instance
```

---

## Schema Bridge Timeline

```
pack_62 (Feb 2025):
  CREATE TABLE deals (id, ext_id, created_ts, address, city, ...)
  PURPOSE: Underwriter focus
  STATUS: Production

ORM Design (Unknown date):
  Expected TABLE: deals (id, created_ts, updated_ts, lead_id, title, stage, ...)
  PURPOSE: Lead-to-deal pipeline
  STATUS: Never reconciled with pack_62

2026-03-30:  
  20260330_add_updated_ts_to_deals ✅ Deploys
  (Now: id, ext_id, created_ts, updated_ts, address, ...)

2026-03-31 03:32:
  20260330_add_lead_id_to_deals (Deploys)
  (Now: id, ext_id, created_ts, updated_ts, lead_id, address, ...)
  
  20260330_add_deal_pipeline_columns (Deploys)
  (Final: Full schema compatibility - pack_62 underwriter columns + ORM pipeline columns)
```

---

## Risk Assessment

### Data Integrity: ✅ LOW
- Migrations only ADD columns (never destructive)
- Existing data preserved
- New columns have nullable/default values
- No data loss

### Backward Compatibility: ✅ HIGH
- pack_62 underwriter features still work (ext_id, address, etc. columns untouched)
- ORM features now work (lead_id, title, stage columns added)
- Both use cases coexist in same table

### Performance: ✅ NO IMPACT
- Index added on lead_id for query performance
- No query rewrites needed
- Schema changes are structural, not data movement

---

## Next Steps

1. **Wait for Render deployment:** Migrations deploy automatically with code push
2. **Monitor Render logs:** Look for migration execution messages
3. **Test endpoints:** Verify GET /health and GET /api/deals
4. **WeWeb retry:** Once GET /api/deals returns 200, inform WeWeb to retry Deals List integration

---

## Deployment Info

- **Commit 1:** ffb4a52 - lead_id migration + intake model fix
- **Commit 2:** a7de432 - Base import fix
- **Commit 3:** 1e5a782 - pipeline columns migration
- **Branch:** main
- **Deployment Target:** https://valhalla-api-ha6a.onrender.com
- **Expected Deploy Time:** 5-10 minutes from push

---

## Questions to Answer if Issue Persists

1. Are migrations executing  in Render? Check: "Migrations completed successfully" in logs
2. Did add_lead_id migration run? Check: "Added lead_id column" in logs
3. Did add_deal_pipeline_columns migration run? Check: All 8 columns added
4. What error appears after each migration stage? (See verification checklist)
5. Are there rows in the deals table? `SELECT COUNT(*) FROM deals;`
