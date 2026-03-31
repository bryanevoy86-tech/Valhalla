# DEAL ORM DOUBLE TIMESTAMP MAPPING FIX

**Status:** ✅ Fix Deployed | ❌ Endpoint Still 500  
**Commit:** `d5c4af0` (double-mapping fix)  
**Date:** 2026-03-30 21:55 UTC

---

## Root Cause Identified

### The Problem

Multiple ORM Deal classes were mapping to the **same `deals` table** with different timestamp column definitions:

**Class 1:** `services/api/app/deals/models.py`
```python
class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}  # ← MERGE INSTRUCTION
    
    created_ts = Column(DateTime, ...)
    updated_ts = Column(DateTime, ...)
```

**Class 2:** `services/api/app/models/deal.py`
```python
class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}  # ← MERGE INSTRUCTION
    
    created_at = Column(DateTime, ...)  # ← LEGACY (doesn't exist in DB)
    updated_at = Column(DateTime, ...)  # ← LEGACY (doesn't exist in DB)
```

### SQLAlchemy Behavior

When multiple classes map to the same table with `extend_existing=True`, SQLAlchemy **merges** the column definitions from both classes.

Result: The Deal ORM was configured to select:
```sql
SELECT ..., deals.created_at, deals.updated_at, deals.created_ts, deals.updated_ts, ...
FROM deals
```

Postgres error: `UndefinedColumn: column deals.created_at does not exist`

---

## The Fix

### File Changed

**File:** `services/api/app/models/deal.py`

**Before:**
```python
class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    ...
```

**After:**
```python
class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    created_ts = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_ts = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    ...
```

### What Changed

- Line 15: `created_at` → `created_ts`
- Line 16: `updated_at` → `updated_ts`

---

## Verification: Generated SQL

### Before Fix

```sql
SELECT deals.id, 
       deals.created_at,         ← LEGACY (error)
       deals.updated_at,         ← LEGACY (error)
       deals.created_ts,         ← NEW (correct)
       deals.updated_ts,         ← NEW (correct)
       ... other columns ...
FROM deals
LIMIT ? OFFSET ?
```

### After Fix

```sql
SELECT deals.id, 
       deals.created_ts,         ✅
       deals.updated_ts,         ✅
       ... other columns ...
FROM deals
LIMIT ? OFFSET ?
```

**Result:** Only canonical `_ts` columns in generated SQL ✅

---

## Test Results After Deployment

```
Commit: d5c4af0
Date: 2026-03-30 21:55 UTC

GET /health:     200 ✅
GET /api/deals:  500 ❌ (correlation_id: 8003d0f4-0cf0-4847-9fdb-f8ae24653c3b)
```

---

## Status

✅ **ORM Fix:** Complete  
✅ **SQL Generation:** Corrected (only `_ts` columns)  
✅ **Code Deployed:** Committed and pushed  
❌ **Endpoint:** Still returning 500  

### Interpretation

The double-timestamp mapping is fixed, but the endpoint is still failing.

**Next Steps:** Check error logs for the actual runtime error on production after the ORM fix was deployed.

The error logging I added to the endpoint should be visible in Render logs with correlation_id: `8003d0f4-0cf0-4847-9fdb-f8ae24653c3b`

---

## Impact Assessment

### Fixed Issues

- ✅ ORM no longer trying to select non-existent `created_at`/`updated_at` columns
- ✅ Generated SQL is now correct and matches production database schema
- ✅ Multiple Deal class definitions now aligned to same column names

### Potential Remaining Issues

- ❌ Endpoint still returns 500
- ❌ Could be database connectivity
- ❌ Could be a different error entirely

The error message will be in Render logs.

