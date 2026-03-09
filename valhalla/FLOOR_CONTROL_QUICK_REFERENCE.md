# Floor Control Plane - Quick Reference

## Files Created ✅

### Models (4 files)
- ✅ `services/api/app/models/income_engine.py` - Engine registry
- ✅ `services/api/app/models/engine_activation_rule.py` - Activation gates
- ✅ `services/api/app/models/revenue_ledger.py` - Revenue tracking with 90/10 split
- ✅ `services/api/app/models/trajectory_target.py` - Monthly targets

### Schemas (1 file)
- ✅ `services/api/app/schemas/floor_control.py` - All input/output schemas

### Services (1 file)
- ✅ `services/api/app/services/floor_control.py` - Business logic

### Routers (1 file)
- ✅ `services/api/app/routers/floor_control.py` - 4 API endpoints

### Migration (1 file)
- ✅ `services/api/alembic/versions/20260205_add_floor_control_plane.py`

### Documentation (3 files)
- ✅ `tools/audit_missing_routers.py` - Module audit script
- ✅ `FLOOR_CONTROL_PLANE_IMPLEMENTATION.md` - Full documentation
- ✅ This file

### Modified (1 file)
- ✅ `services/api/app/main.py` - Added floor_control router registration

---

## 4 API Endpoints

```
POST   /api/governance/floor/engines/upsert
       Register or update an income engine

POST   /api/governance/floor/revenue/record
       Log revenue with automatic 10% fun fund split

POST   /api/governance/floor/targets/upsert
       Set monthly targets for floor enforcement

GET    /api/governance/floor/trajectory/month?month=YYYY-MM-DD&engine_code=SYSTEM
       Check actual vs target with variance alerts
```

---

## Deployment Checklist

- [ ] Review `FLOOR_CONTROL_PLANE_IMPLEMENTATION.md`
- [ ] Run audit: `python tools/audit_missing_routers.py`
- [ ] Migrate: `cd services/api && alembic upgrade head`
- [ ] Start app (router auto-registers)
- [ ] Test endpoints with curl/Postman
- [ ] Register your income engines
- [ ] Set monthly targets
- [ ] Start logging revenue
- [ ] Monitor with trajectory endpoint

---

## 195 Missing Modules Found

Use `python tools/audit_missing_routers.py` to see full list.

Most common failures:
- AttributeError: Module doesn't exist yet
- ValidationError: Missing environment variables (DATABASE_URL, VALHALLA_JWT_SECRET)
- ModuleNotFoundError: Typo in import path

---

## Revenue Split Example

```
Income Event:
  engine_code: "REAL_ESTATE_WHOLESALE"
  gross_amount: $100,000
  as_of_date: 2026-02-05

Automatic Split:
  Fun Fund (10%):        $10,000  ← Goes to fun fund bucket
  Reinvest (90%):        $90,000  ← Goes to operations
  Ops Reserve (0%):      $0        ← Available for future use

All tracked in revenue_ledger with full audit trail.
```

---

## Monthly Trajectory Example

```
Target Set:
  month: 2026-02-01
  min_gross: $450,000
  min_fun_fund: $45,000

Actual Results (Feb 2026):
  actual_gross: $425,000
  actual_fun_fund: $42,500

Status:
  gross_delta: -$25,000  (SHORT)
  fun_fund_delta: -$2,500 (SHORT)
  severity: "WARNING"     (not yet CRITICAL)

Note: Goes to CRITICAL if fun_fund is >10% below target
```

---

## Quick Test

```bash
# 1. Register an engine
curl -X POST http://localhost:8000/api/governance/floor/engines/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST_ENGINE",
    "name": "Test",
    "category": "TESTING",
    "status": "TESTING"
  }'

# 2. Record revenue
curl -X POST http://localhost:8000/api/governance/floor/revenue/record \
  -H "Content-Type: application/json" \
  -d '{
    "engine_code": "TEST_ENGINE",
    "gross_amount": 10000,
    "as_of_date": "2026-02-05"
  }'

# 3. Check trajectory
curl "http://localhost:8000/api/governance/floor/trajectory/month?month=2026-02-01"
```

---

**Status:** ✅ READY FOR DEPLOYMENT  
**Date:** February 5, 2026
