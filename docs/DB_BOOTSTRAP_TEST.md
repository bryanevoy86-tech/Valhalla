# Database Bootstrap Test - Sprint 2

**Status**: ✅ SUCCESSFUL  
**Date**: 2026-03-26  
**Result**: Fresh database bootstrap working with core pipeline schema

---

## Empty DB Setup Steps

### 1. Clean Slate
```bash
# Remove existing database
rm valhalla_local.db

# Verify it's gone
ls -la valhalla_local.db  # should not exist
```

### 2. Environment Verification
```bash
# Ensure .env is properly configured
cat .env | grep DATABASE_URL
# Expected: DATABASE_URL=sqlite:///./valhalla_local.db

cat .env | grep VALHALLA_JWT_SECRET
# Expected: VALHALLA_JWT_SECRET=dev-secret-key-change-in-production
```

---

## Migration Commands & Results

### Original Approach (FAILED)
**Command**: `alembic upgrade head`  
**Result**: ❌ FAILED - Multiple broken migration chains

**Blocker**: Migration revision `0068_pack_tq_tr_ts_tt.py` referenced non-existent revision `0067`

**Root Cause**: Historical alembic migrations had:
- Multiple format mixing (numeric, UUID, date-based)
- Broken revision chains (orphaned migrations)
- Missing referenced parents in migration graph
- Unresolved merge conflicts from previous work

### Fix Applied
**File Modified**: `alembic/env.py`
- Added `.env` loading before model imports: `from dotenv import load_dotenv; load_dotenv()`
- Set up module aliasing: `sys.modules['app'] = import_module('services.api.app')`
- Fixed Base import to use canonical path: `from services.api.app.core.db import Base`

**Migration Chain Repair**:
- Fixed `0068_pack_tq_tr_ts_tt.py` down_revision to reference last valid parent: `fdc9b660a48f`
- Decision: Did NOT attempt full repair of 53-migration chain (too fragile)

### New Approach (SUCCESS)
**Bootstrap Script**: `db_bootstrap.py`  
**Command**: `python db_bootstrap.py`

**Approach**:
- Bypass broken alembic chain entirely
- Use raw SQL DDL via SQLAlchemy to create tables directly
- Focus ONLY on core pipeline schema (8 tables)
- Provides clean slate without migration dependencies

**Output**:
```
✅ Database verified: 8 tables present
   - audit_logs
   - buyer_matches
   - buyers
   - contracts
   - deal_stage_history
   - deals
   - leads
   - offers
```

---

## Final Status After Bootstrap

### Database Properties
- **Engine**: SQLite (Local development)
- **Location**: `d:\dev\valhalla_local.db`
- **Size**: ~20 KB (8 core tables)
- **Timestamp Support**: Automatic via SQL defaults

### Core Tables Created
1. **leads** - Acquisition and intake pipeline
2. **deals** - Deal opportunity records
3. **offers** - Offer generation and tracking  
4. **buyers** - Buyer profiles and cash readiness
5. **contracts** - Legal contract management
6. **audit_logs** - Comprehensive action trail
7. **buyer_matches** - Deal-buyer matching history
8. **deal_stage_history** - Stage transition audit trail

### Schema Features
- All tables have `id` (auto-increment primary key)
- All tables have `created_at` and `updated_at` (with SQL defaults)
- Foreign keys enforce referential integrity:
  - `deals.lead_id` → `leads.id`
  - `offers.deal_id` → `deals.id`
  - `contracts.deal_id` → `deals.id`
  - `contracts.offer_id` → `offers.id`
  - `buyer_matches.deal_id` → `deals.id`
  - `buyer_matches.buyer_id` → `buyers.id`
  - `deal_stage_history.deal_id` → `deals.id`

### Ready for Development
- ✅ Persistent storage for 6 core entities
- ✅ Audit trail for compliance
- ✅ Buyer matching infrastructure
- ✅ Deal lifecycle tracking
- ✅ No dependency on broken migrations

---

## Bootstrap Commands (Sprint 2 Onwards)

### To bootstrap a fresh development database:
```bash
cd d:\dev
python db_bootstrap.py
```

### To verify database connectivity:
```bash
python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///./valhalla_local.db')
inspector = inspect(engine)
print(f'Tables: {inspector.get_table_names()}')
"
```

### To start the app after bootstrap:
```bash
. .venv/Scripts/Activate.ps1
python -m uvicorn app.main:app --reload --port 4000
```

---

## Next Steps (Sprint 2)

### Immediate
1. ✅ Bootstrap complete - fresh DB ready
2. → Wire Lead router to persistent table
3. → Build Deal model/service/router on persistent storage
4. → Build Offer model/service/router on persistent storage
5. → Migrate Buyer from in-memory to persistent
6. → Add Dashboard/Audit routers
7. → Create comprehensive smoke tests

### Future (Post-Sprint 2)
- Consider whether to keep or migrate from `db_bootstrap.py` approach
- If keeping: document as official bootstrap method
- If migrating: rebuild alembic migration chain health from scratch

---

## Lessons Learned

### What Worked
- ✅ Raw SQL DDL approach is pragmatic for clean bootstrap
- ✅ Bypassing broken alembic chain prevents cascading failures
- ✅ Focus on core schema first reduces complexity

### What To Avoid
- ❌ Don't try to fix deeply broken migration chains during sprint work
- ❌ Don't assume models/__init__.py will auto-register all metadata
- ❌ Don't depend on complex import aliasing during initialization

### Recommendation
For future projects or major refactors:
1. Keep migration chain simpler (fewer files, clearer dependencies)
2. Document migration format decisions upfront
3. Version migrations consistently (don't mix UUID + numeric + date formats)
4. Test bootstrap from empty database regularly (CI/CD)
5. Keep a bootstrap fallback (like this SQL DDL script) always available

---

**Status**: Fresh database ready for Sprint 2 core pipeline development  
**Command to replicate**: `python db_bootstrap.py`  
**Expected result**: 8-table core schema, ready to accept data
