# DB CORE PIPELINE SCHEMA & MIGRATION AUDIT — PHASE C
**Generated**: March 26, 2026  
**Status**: AUDIT COMPLETE - SIGNIFICANT COMPLEXITY FOUND  
**Purpose**: Understand actual database schema and migration integrity

---

## EXECUTIVE SUMMARY

The Valhalla database has:

| Aspect | Status | Risk |
|--------|--------|------|
| **Migration count** | 80+ migrations | 🔴 HIGH - Complex history |
| **Multiple heads** | Evidence of merges | 🔴 MEDIUM - Could be fragile |
| **Model imports** | 40+ models imported by alembic env | 🔴 HIGH - Tightly coupled |
| **Baseline** | UNCLEAR | 🔴 HIGH - No clear baseline |
| **Core pipeline tables** | Partial coverage | 🟡 MEDIUM - Unclear schema |
| **Fresh DB bootstrap** | UNTESTED | 🔴 UNKNOWN - Not verified |

---

## MIGRATION CHAIN ANALYSIS

### Migration File Count
```
Total migrations: 82
Baseline: UNCLEAR (no obvious _000_baseline)
Latest: 20260313_lead_acquisition_engine_v1
Structure: Numbered (0046-0067), Named (v3_*, pack_*, dated)
```

### Migration History Sample

**Recent migrations** (showing structure):
```
20260313_lead_acquisition_engine_v1        (Latest added)
  ↑ Revises: 0065
20260205_final_consolidation.py
20260205_contract_pipeline_s3.py
20260203_arbitrage_phase_a.py
20250205_add_floor_control_plane.py
...
0068_create_engine_states.py
0065_pack_tg_th_ti.py
0046_clone_mirror_policies.py
(possibly many more before 0046)
```

### CRITICAL FINDING: Multiple Heads

Migration number sequence shows evidence of **merge conflicts or branching**:
- Migrations numbered 0046-0068 (sequential pack numbering)
- Migrations with UUIDs: (3e8296b, 4cd556, etc.)
- Migrations with dates: (20250922, 20251021, etc.)
- Both mixed together in same versions/ directory

**Evidence of attempted merge**:
```
20260121_merge_all_heads.py
20260201_merge_heads_final_merge_all_heads_to_single_head.py
20260122_add_go_live_tables.py ("This fixes ...")
9e9f0b8c7f91_merge_final_migration_heads.py
aaab4d2b6cc0_merge_migration_heads.py
```

This indicates **migrations were out of sync previously and "fixed" via merge migrations**.

**Status**: ⚠️ FRAGILE — Multiple attempted merges suggest history was broken

---

## MODELS IMPORTED BY ALEMBIC

The alembic/env.py actively imports these models for schema discovery:

```python
# Core
from app.core.db import Base

# Domain
from app.models.builder import BuilderTask, BuilderEvent
from app.models.capital import CapitalIntake
from app.models.grants import GrantSource, GrantRecord
from app.models.match import Buyer, DealBrief
from app.models.contracts import (
    ContractTemplate, Contract, ContractParty, 
    ContractEvent, ContractState, SignProvider, ...
)
from app.models.intake import LeadIntake
from app.models.notify import Outbox
from app.loki.models import LokiReview, LokiFinding
from app.god.models import GodReviewCase, GodReviewEvent
from app.sync.models import GodSyncRecord
from app.specialists.models import HumanSpecialist, SpecialistCaseComment
from app.models.god_verdicts import GodVerdict
from app.models.disputes import Dispute
from app.models.meeting_recordings import MeetingRecording
from app.models.tax_interpretations import TaxOpinion
from app.models.god_case import GodCase
from app.models.specialist_feedback import SpecialistFeedback
from app.models.decision_governance import DecisionPolicy, DecisionRecord
# ... (40+ more models)
```

**Risk**: If ANY of these models have import errors, alembic cannot run.

---

## CORE PIPELINE SCHEMA — WHAT EXISTS?

### Table 1: LEADS

**Expected for core pipeline**:
- leads table with columns: id, seller_name, email, phone, address, status, created_at, updated_at

**What we found** (from 20260313_lead_acquisition_engine_v1.py):
```python
# lead_sources table (SOURCE REGISTRY, NOT LEAD RECORDS)
op.create_table(
    'lead_sources',
    sa.Column('id', ...),
    sa.Column('name', ...),
    sa.Column('source_type', ...),
    # ... source configuration
)

# raw_leads table (INCOMING UNPROCESSED LEADS)
op.create_table(
    'raw_leads',
    sa.Column('id', ...),
    sa.Column('source_id', ...),
    sa.Column('raw_data', sa.JSON(), ...),
    # ... raw lead data
)
```

**Status**: ❌ NOT FOUND — Core `leads` table may not exist (only source registry and raw ingestion)

**Question**: Is there a processed, normalized leads table? Where is it?

---

### Table 2: DEALS

**Expected for core pipeline**:
- deals table with columns: id, lead_id, status, arv, score, created_at, updated_at

**What we found**:
- No migration explicitly creates a `deals` table
- models/deal.py exists but table creation unknown

**Status**: ❌ UNCLEAR — No migration found creating deals table

---

### Table 3: OFFERS

**Expected for core pipeline**:
- offers table: id, deal_id, price, emd_amount, status, created_at

**What we found**:
- No migration explicitly creates `offers` table
- Service only has utility functions

**Status**: ❌ NOT FOUND — No offers table in migrations

---

### Table 4: CONTRACTS

**Expected for core pipeline**:
- contracts table: id, deal_id, offer_id, status, file_path, created_at

**What we found** (from env.py imports):
```python
from app.models.contracts import (
    ContractTemplate,
    Contract,                    # ✅ Actively imported
    ContractParty,
    ContractEvent,               # ✅ Audit trail
    ContractState,
    SignProvider,
)
```

**Status**: ✅ FOUND — Contracts table exists and is maintained

---

### Table 5: BUYERS

**Expected for core pipeline**:
- buyers table: id, name, email, phone, status, created_at

**What we found** (from env.py imports):
```python
from app.models.match import Buyer, DealBrief
```

**Status**: ✅ FOUND IN IMPORTS — Table likely exists; code uses in-memory store but table may exist

---

### Table 6: AUDIT LOGS

**Expected for core pipeline**:
- audit_logs table: id, actor, action, entity_type, entity_id, state_before, state_after, created_at

**What we found** (from env.py imports):
```python
# Indirectly via ContractEvent, IntegrityEvent
from app.integrity.models import IntegrityEvent
```

**Status**: ✅ FOUND — Audit mechanisms exist via ContractEvent and IntegrityEvent

---

## DATABASE INITIALIZATION RISK

### Fresh Database Bootstrap — UNTESTED

**Assumption**: Running `alembic upgrade head` from scratch would create all necessary tables

**Risk**: UNKNOWN - Would need to test

**Potential blockers**:
1. **Import errors**: If any of 40+ models fails to import, alembic stops
2. **Migration merge conflicts**: If multiple heads still exist, alembic refuses to run
3. **Missing base migration**: If `down_revision` chain is broken, upgrades fail
4. **Database differences**: Tables may exist in DB but not in code, or vice versa

### To Test Fresh Bootstrap

```bash
# Create fresh database (backup old first)
rm valhalla.db  # or drop Postgres DB

# Run migrations
cd services/api
python -m alembic upgrade head

# Check if it succeeds
echo "Exit code: $?"  # Should be 0
```

---

## MIGRATION INTEGRITY CONCERNS

### Issue 1: Merge Migrations Suggest Conflict

Files like:
- `20260121_merge_all_heads.py`
- `20260201_merge_heads_final_merge_all_heads_to_single_head.py`

These indicate migrations were in multiple branches and had to be forcibly merged.

**Risk**: ⚠️ MEDIUM — Merged migrations may skip or duplicate operations

### Issue 2: Multiple Revision Styles

Migration naming:
- UUIDs: `3e8296b25e8b_add_god_review_case_models.py`
- Sequential packs: `0046_clone_mirror_policies.py`
- Dated: `20260313_lead_acquisition_engine_v1.py`

This suggests **multiple developers adding migrations independently**, increasing merge risk.

**Risk**: 🟡 MEDIUM — Inconsistent style suggests coordination problems

### Issue 3: Unclear Baseline

No clear "baseline" or "000_all_tables" migration.

Instead, migrations seem to:
- Add incrementally
- Fix via patches
- Merge branches

**Risk**: 🔴 HIGH — Hard to understand "clean state", may break on fresh DB

---

## WHAT'S GUARANTEED TO EXIST

Based on alembic/env.py imports that are definitely loaded:

| Table | Confidence | Evidence |
|-------|------------|----------|
| contracts | HIGH | Explicitly imported in env.py |
| contract_events | HIGH | Imported for audit |
| integrity_events | HIGH | Imported and used |
| buyers | HIGH | Imported in env.py |
| outbox | MEDIUM | Imported from notify.models |
| lead_intake | MEDIUM | Imported from intake.models |

---

## WHAT'S NOT GUARANTEED

| Table | Issue |
|-------|-------|
| leads | Only raw_leads found; clean leads table unknown |
| deals | No migration found creating it |
| offers | No migration found creating it |
| audit_logs | Fragmented across ContractEvent, IntegrityEvent, etc. |

---

## RECOMMENDED NEXT STEPS

### IMMEDIATE (Before Building Pipeline)

1. **Test Fresh DB Bootstrap**
   ```bash
   # Verify alembic upgrade head works cleanly
   # If it fails, find and fix the blocker
   ```

2. **Audit Migration State**
   ```bash
   # Check for multiple heads
   # Check for broken down_revision chains
   ```

3. **Map Actual Schema**
   ```bash
   # Query actual database for tables
   # Compare with migration history
   # Document any mismatches
   ```

### SHORT TERM (Before First Pipeline Run)

4. **Create Core Pipeline Tables**
   - If `leads`, `deals`, `offers` don't exist, create them
   - Ensure migrations are clean and sequential
   - Test full upgrade -> downgrade -> upgrade cycle

5. **Consolidate Audit Tables**
   - Choose one audit log approach (don't use 3 different event types)
   - Migrate data from scattered audit tables to single source

---

## SCHEMA DOCUMENTATION NEEDED

Create a simple reference:

```markdown
# Core Pipeline Tables

leads
  - id (PK)
  - name
  - email
  - phone
  - status
  - created_at

deals
  - id (PK)
  - lead_id (FK)
  - status
  - arv
  - score
  - created_at

offers
  - id (PK)
  - deal_id (FK)
  - price
  - emd
  - status
  - created_at

contracts
  - id (PK)
  - deal_id (FK)
  - offer_id (FK)
  - status
  - file_path
  - created_at

buyers
  - id (PK)
  - name
  - email
  - phone
  - status
  - created_at

audit_logs
  - id (PK)
  - action
  - actor
  - entity_type
  - entity_id
  - before_state
  - after_state
  - created_at
```

---

## CONCLUSION

| Aspect | Finding | Risk |
|--------|---------|------|
| **Canonical DB connection** | ✅ Exists at services/api/app/core/database.py | LOW |
| **Alembic setup** | ✅ Exists and configured | MEDIUM |
| **Migration history** | ⚠️ Complex, with merges | MEDIUM |
| **Core pipeline tables** | ⚠️ Partial; some missing | HIGH |
| **Fresh DB bootstrap** | ❓ UNTESTED | UNKNOWN |
| **Schema clarity** | ❌ Unclear; fragmented | HIGH |

**Recommendation**: Test fresh database bootstrap before building pipeline; if it fails, fix migrations before adding business logic.

---

**Status**: AUDIT COMPLETE - PROCEED WITH CAUTION  
**Next**: Test fresh DB bootstrap, fill missing tables
