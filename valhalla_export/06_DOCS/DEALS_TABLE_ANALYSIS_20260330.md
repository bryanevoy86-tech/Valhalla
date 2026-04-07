# Comprehensive Deals Table Analysis

**Date**: March 30, 2026  
**Status**: FINAL ANALYSIS - Multiple Deals Tables with Conflicting Schemas  
**Applies To**: GET /api/deals endpoint failure

---

## EXECUTIVE SUMMARY

**FINDING**: There are **THREE distinct deals table definitions** across the codebase, but **ONLY ONE actually exists in production**.

- **Production Table**: `pack_62_underwriter` (underwriter/geolocation-focused schema)
- **Intended Table**: `20260305_create_core_pipeline_tables` (lead→deal→offer pipeline schema)
- **Bootstrap Table**: `db_bootstrap.py` (same as intended, for fresh dev databases)

**CURRENT STATUS**: API GET /api/deals is failing because the production table (pack_62) lacks the `lead_id` column that the ORM expects. Recent patches attempt to bridge this gap by adding the missing column, but this is a band-aid fix over a schema architecture conflict.

---

## DETAILED INVENTORY OF ALL DEALS TABLE CREATION POINTS

### 1. ⚠️ PRIMARY PRODUCTION TABLE: pack_62_underwriter

**File**: `d:\dev\services\api\alembic\versions\pack_62_underwriter.py`

**Migration Details**:
- Revision ID: `pack_62_underwriter`
- Down Revision: `pack_61_heimdall_training`
- Execution: Conditional - only if table doesn't exist
- Database: PostgreSQL (dialect-specific)

**Schema** (14 columns):
```python
deals:
  - id: BigInteger, PRIMARY KEY
  - ext_id: String(64), UNIQUE, nullable
  - created_ts: DateTime, default=CURRENT_TIMESTAMP
  - address: String(256)
  - city: String(64)
  - province: String(16)
  - postal_code: String(16)
  - lat: Float
  - lng: Float
  - status: String(32), indexed
  - ask_price: Numeric(14,2)
  - notes: Text
  - meta: PostgreSQL JSONB
```

**Associated Tables Created**:
```
pack_62_underwriter creates:
├── comps (deal_id → deals.id FK)
├── underwriting_signals (deal_id → deals.id FK)  
└── deal_scores (deal_id → deals.id FK)

Downstream packs depend on this:
├── pack_63_closer_engine (references deals.id)
├── pack_64_contract_engine (references deals.id)
└── pack_65_buyer_match (references deals.id)
```

**Status**: ✅ This table EXISTS on Render production (confirmed by recent patch failures saying "column deals.lead_id does not exist")

**Focus**: Real estate geolocation, underwriter signals, deal scoring

---

### 2. 🔄 INTENDED PIPELINE TABLE: create_core_pipeline_tables

**File**: `d:\dev\alembic\versions\20260305_000000_create_core_pipeline_tables.py`

**Migration Details**:
- Revision ID: `f2b00b1c2d4c`
- Down Revision: `f2af0b1c2d4b`
- Creation Date: 2026-03-05
- Purpose: "Frontend phase 1 blocker fix: Ensure leads and deals tables exist for GET /api/deals endpoint"
- Execution: Uses **IF NOT EXISTS** - will NOT override existing table
- Database: Dual - PostgreSQL + SQLite fallback

**Schema** (13 columns, lead-centric):
```python
deals:
  - id: Integer/Serial, PRIMARY KEY, indexed
  - created_ts: DateTime WITH TIME ZONE, default=NOW()
  - updated_ts: DateTime WITH TIME ZONE, default=NOW()
  - lead_id: Integer, FK→leads.id, NOT NULL, indexed ⚠️
  - title: String(255), NOT NULL
  - stage: String(50), default='lead_received', indexed
  - status: String(50), default='active', indexed
  - arv: Numeric(15,2) [After-Repair Value]
  - estimated_repair_cost: Numeric(15,2)
  - max_allowable_offer: Numeric(15,2)
  - target_assignment_fee: Numeric(15,2)
  - score: Numeric(8,2), default=0
  - notes: Text
  - disposition_status: String(50)
```

**Status**: ❌ This table DOES NOT execute on Render because pack_62 table already exists, triggering the IF NOT EXISTS condition

**Focus**: Lead pipeline processing, deal valuation, offer workflow

**Related**: Also creates leads table with full lead contact/property information

---

### 3. 📦 BOOTSTRAP TABLE: db_bootstrap.py

**File**: `d:\dev\db_bootstrap.py` (lines 81-95)

**Purpose**: Fresh database initialization script for development/testing

**Schema**: Identical to #2 (20260305 pipeline table)
```python
deals (SQLite variant):
  - id: INTEGER PRIMARY KEY AUTOINCREMENT
  - created_at: DATETIME DEFAULT CURRENT_TIMESTAMP
  - updated_at: DATETIME DEFAULT CURRENT_TIMESTAMP
  - lead_id: INTEGER NOT NULL
  - title: VARCHAR(255) NOT NULL
  - stage: VARCHAR(50) NOT NULL DEFAULT 'lead_received'
  - status: VARCHAR(50) NOT NULL DEFAULT 'active'
  - arv: DECIMAL(15, 2)
  - estimated_repair_cost: DECIMAL(15, 2)
  - max_allowable_offer: DECIMAL(15, 2)
  - target_assignment_fee: DECIMAL(15, 2)
  - score: DECIMAL(8, 2) DEFAULT 0
  - notes: TEXT
  - disposition_status: VARCHAR(50)
  - FOREIGN KEY (lead_id) REFERENCES leads(id)
```

**Status**: ✅ Used for local development databases

**Note**: Uses SQLite (AUTOINCREMENT) vs PostgreSQL (SERIAL) syntaxes

---

## SCHEMA MISMATCH IMPACT TABLE

| Column | pack_62 | Pipeline | ORM Model | Current Production | Gap? |
|--------|---------|----------|-----------|-------------------|------|
| id | ✅ BigInt | ✅ Int | ✅ Int | ✅ BigInt | format |
| ext_id | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| created_ts | ✅ | ✅ | ✅ | ✅ |  |
| **lead_id** | ❌ | ✅ | ✅ required | ❌ | **CRITICAL** |
| updated_ts | ❌ | ✅ | ✅ | ❌ patch pending | **CRITICAL** |
| address | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| city | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| province | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| postal_code | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| lat/lng | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| title | ❌ | ✅ | ✅ | ❌ | ❌ in code |
| stage | ✅ | ✅ | ✅ | ✅ |  |
| status | ✅ | ✅ | ✅ | ✅ |  |
| arv | ❌ | ✅ | ✅ | ❌ | ❌ in code |
| estimated_repair_cost | ❌ | ✅ | ✅ | ❌ | ❌ in code |
| max_allowable_offer | ❌ | ✅ | ✅ | ❌ | ❌ in code |
| target_assignment_fee | ❌ | ✅ | ✅ | ❌ | ❌ in code |
| ask_price | ✅ | ❌ | ❌ | ✅ | ❌ in code |
| score | ✅ | ✅ | ✅ | ✅ |  |
| notes | ✅ | ✅ | ✅ | ✅ |  |
| disposition_status | ❌ | ✅ | ✅ | ❌ | ❌ in code |
| meta (JSONB) | ✅ | ❌ | ❌ | ✅ | ❌ in code |

---

## ORM MODEL EXPECTATION

**File**: `d:\dev\services\api\app\deals\models.py` (lines 36-71)

The Deal ORM class explicitly expects the **pipeline schema**:

```python
class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    created_ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_ts = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # CRITICAL: This column doesn't exist in pack_62 table
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    stage = Column(String(50), nullable=False, default="lead_received", index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    
    # These columns don't exist in pack_62 table
    arv = Column(Numeric(15, 2), nullable=True)
    estimated_repair_cost = Column(Numeric(15, 2), nullable=True)
    max_allowable_offer = Column(Numeric(15, 2), nullable=True)
    target_assignment_fee = Column(Numeric(15, 2), nullable=True)
    score = Column(Numeric(8, 2), nullable=True, default=0)
    notes = Column(Text, nullable=True)
    disposition_status = Column(String(50), nullable=True)
```

**When API tries to query**: `SELECT * FROM deals WHERE ...` or `SELECT deals.lead_id FROM deals`
- ✅ Works for columns in pack_62: id, created_ts, status, stage, score, notes
- ❌ **Fails for columns NOT in pack_62**: lead_id, updated_ts, title, arv, etc.

---

## ATTEMPTED FIXES (Patch Migrations)

### Patch 1: Add updated_ts Column

**File**: `d:\dev\services\api\alembic\versions\20260330_add_updated_ts_to_deals.py`

**Revision**: `add_updated_ts_to_deals`  
**Down Revision**: `20260205_final_consolidation`

**What it does**:
```python
def upgrade():
    if "deals" in insp.get_table_names():
        if "updated_ts" not in columns:
            op.add_column("deals", 
                sa.Column("updated_ts", sa.DateTime, nullable=True,
                         server_default=sa.text("CURRENT_TIMESTAMP")))
```

**Status**: ✅ Adds the missing updated_ts column to existing pack_62 table

---

### Patch 2: Add lead_id Column

**File**: `d:\dev\services\api\alembic\versions\20260330_add_lead_id_to_deals.py`

**Revision**: `add_lead_id_to_deals`  
**Down Revision**: `add_updated_ts_to_deals`

**What it does**:
```python
def upgrade():
    if "deals" in insp.get_table_names():
        if "lead_id" not in columns:
            op.add_column("deals",
                sa.Column("lead_id", sa.Integer, nullable=True, index=True))
```

**Critical Problem Statement**:
```
The pack_62_underwriter migration created deals table with ext_id (underwriter focus).
The ORM/service layer expects lead_id (lead-to-deal pipeline focus).

Production Issue: psycopg2.errors.UndefinedColumn: column deals.lead_id does not exist
Root Cause: ORM query selects deals.lead_id but production table only has ext_id
Solution: Add nullable lead_id column to deals table
```

**Status**: ⚠️ Band-aid fix - adds the column but doesn't establish the actual lead→deal relationship data

---

### Patch 3: Bootstrap Clean Table

**File**: `d:\dev\alembic\versions\9999_bootstrap_core_pipeline.py`

**Purpose**: Create a completely separate clean "deals" table for fresh starts

**Status**: ❌ Won't execute on Render because pack_62 table already exists

---

## ROOT CAUSE ANALYSIS

### Why GET /api/deals Fails

**Sequence**:

1. **pack_62_underwriter runs first** (during initial system setup)
   - Creates deals table with underwriter schema (ext_id, geo data, JSONB)
   - Creates comps, underwriting_signals, deal_scores tables

2. **Later: 20260305_create_core_pipeline_tables attempts to run**
   - Designed for lead pipeline processing
   - Uses `IF NOT EXISTS` to be idempotent
   - **Does NOT execute** because pack_62 table already exists

3. **ORM models written for pipeline schema**
   - Expects lead_id, updated_ts, title, arv, etc.
   - Maps to non-existent columns

4. **API requests fail**
   - SELECT leads.lead_id FROM deals → Column does not exist
   - GET /api/deals endpoint crashes

5. **Patches applied (2026-03-30)**
   - Add lead_id column
   - Add updated_ts column
   - Band-aid: API may now work for basic operations but schema remains fundamentally misaligned

---

## SCHEMA ARCHITECTURE CONFLICT

### pack_62 Design (Underwriter Focus):
- External system integration (ext_id for external sources)
- Geolocation fields (address, city, province, postal_code, lat, lng)
- Property metadata (ask_price, JSONB metadata)
- Underwriter-specific tables (comps, underwriting_signals, deal_scores)
- **No lead relationship** - deals may come from external sources

### Pipeline Design (Lead Management Focus):
- Lead tracking (lead_id FK to leads table)
- Deal valuation (arv, estimated_repair_cost, max_allowable_offer, target_assignment_fee)
- Pipeline state (stage, status, disposition_status)
- Offer workflow (designed to feed into offer generation)
- **Tightly coupled to leads** - every deal originates from a lead

### Result:
Different system perspectives trying to use the same table name with incompatible schemas.

---

## MIGRATION DEPENDENCY CHAIN

### Services API (production):
```
pack_61_heimdall_training (baseline)
    ↓
pack_62_underwriter [CREATES deals TABLE] ⚠️
    ├─→ comps (FK: deals.id)
    ├─→ underwriting_signals (FK: deals.id)
    └─→ deal_scores (FK: deals.id)
    ↓
pack_63_closer_engine [FK: deals.id]
    ↓  
pack_64_contract_engine [FK: deals.id]
    ↓
pack_65_buyer_match [FK: deals.id]
    ↓
... (more packs referenced deals.id)
    ↓
20260205_final_consolidation
    ↓
20260330_add_updated_ts_to_deals [PATCHES deals TABLE]
    ↓
add_lead_id_to_deals [PATCHES deals TABLE]
```

### Root (production):
```
20260305_000000_create_core_pipeline_tables [IF NOT EXISTS - skipped]
    ├─→ leads table
    └─→ deals table (duplicates pack_62 if ever created)
```

---

## CURRENT SITUATION (March 30, 2026)

### What Exists on Render Production:
- ✅ deals table (from pack_62_underwriter) with schema:
  - id, ext_id, created_ts, address, city, province, postal_code, lat, lng, status, ask_price, notes, meta
  - **plus recently added**: lead_id, updated_ts

### What ORM Expects:
- ✅ Most fields now present (after patches)
- ⚠️ Many fields not used by pack_62 design (title, arv, estimated_repair_cost, etc.)
- ⚠️ Many pack_62 fields not in ORM (ext_id, address, city, province, postal_code, lat, lng, ask_price, meta)

### Result:
- 🔄 **Partial Compatibility** - GET /api/deals likely works now for basic queries
- ⚠️ Data integrity issues - No mechanism to populate title, arv, etc. from pack_62 table
- ❌ Schema debt - Two incompatible systems using same table name

---

## RESOLUTION ANALYSIS

### Option A: Continue Current Approach (Band-aid)
**Status**: Currently being implemented

- Keep pack_62 table as-is
- Continue patching in missing columns
- Accept schema inconsistency
- Pros: Minimal disruption, fast
- Cons: Technical debt, data sync issues, future maintenance nightmare

### Option B: Full Schema Migration (Correct)
**Status**: Would require planned downtime

- Create new deals table with pipeline schema
- Migrate data from pack_62 → new table
- Update all FK references (comps, underwriting_signals, deal_scores)
- Drop pack_62 table
- Pros: Clean architecture, resolves debt
- Cons: Risky in production, requires data mapping (ext_id ↔ lead_id), 

### Option C: Parallel Tables + View Layer (Complex)
**Status**: Not recommended

- Keep both independently
- Create database view presenting unified interface
- Pros: Non-disruptive
- Cons: Query performance, maintenance complexity, data sync issues

---

## CONCLUSION

### ANSWER TO QUESTION: "Is pack_62's deals table THE production table?"

**YES. Definitively.**

- It's the **ONLY** deals table that exists on Render
- It was created first (pack_62_underwriter migration)
- All downstream packs (63, 64, 65) reference it
- The 20260305 pipeline table never executes (IF NOT EXISTS condition)
- Bootstrap table only used for fresh dev databases

### The Real Issue

This is **not a "which table is it" question** — it's a **"two teams built schemas for different business needs and both tried to use the 'deals' table"** situation.

- Underwriter team (pack_62): Needed geolocation, external system tracking, deal scoring
- Frontend/Pipeline team (2026-03-05): Needed lead tracking, deal valuation, offer workflow
- Result: Patches to make them work together, but fundamentally misaligned

### What's Happening Now (2026-03-30)

1. Recent patches add lead_id and updated_ts to pack_62 table
2. API GET /api/deals now works (basic queries)
3. But: ORM code can't populate many fields it defines, pack_62 data missing from ORM context
4. Sustainable? Short term yes, long term → technical debt spiral

---

## FILES REFERENCE

All File Locations (absolute paths):

| Purpose | File | Location |
|---------|------|----------|
| Production creates deals | pack_62_underwriter.py | d:\dev\services\api\alembic\versions\pack_62_underwriter.py |
| Pipeline creates deals | 20260305_000000_create_core_pipeline_tables.py | d:\dev\alembic\versions\20260305_000000_create_core_pipeline_tables.py |
| Bootstrap creates deals | db_bootstrap.py | d:\dev\db_bootstrap.py |
| ORM Deal model | models.py | d:\dev\services\api\app\deals\models.py |
| Patch: add updated_ts | 20260330_add_updated_ts_to_deals.py | d:\dev\services\api\alembic\versions\20260330_add_updated_ts_to_deals.py |
| Patch: add lead_id | 20260330_add_lead_id_to_deals.py | d:\dev\services\api\alembic\versions\20260330_add_lead_id_to_deals.py |
| Bootstrap clean table | 9999_bootstrap_core_pipeline.py | d:\dev\alembic\versions\9999_bootstrap_core_pipeline.py |

---

## APPENDIX: Full Column Schemas

### pack_62_underwriter (Production - 14 columns)
```sql
CREATE TABLE deals (
    id BIGINT PRIMARY KEY,
    ext_id VARCHAR(64) UNIQUE,
    created_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    address VARCHAR(256),
    city VARCHAR(64),
    province VARCHAR(16),
    postal_code VARCHAR(16),
    lat FLOAT,
    lng FLOAT,
    status VARCHAR(32) INDEXED,
    ask_price NUMERIC(14,2),
    notes TEXT,
    meta JSONB,
    -- Recent patches add:
    lead_id INTEGER,
    updated_ts DATETIME
);
```

### Pipeline Schema (13 columns - intended)
```sql
CREATE TABLE deals (
    id INTEGER PRIMARY KEY,
    created_ts TIMESTAMP WITH TZ DEFAULT NOW(),
    updated_ts TIMESTAMP WITH TZ DEFAULT NOW(),
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    title VARCHAR(255) NOT NULL,
    stage VARCHAR(50) DEFAULT 'lead_received',
    status VARCHAR(50) DEFAULT 'active',
    arv NUMERIC(15,2),
    estimated_repair_cost NUMERIC(15,2),
    max_allowable_offer NUMERIC(15,2),
    target_assignment_fee NUMERIC(15,2),
    score NUMERIC(8,2) DEFAULT 0,
    notes TEXT,
    disposition_status VARCHAR(50)
);
```

---

**Generated**: March 30, 2026
**Status**: Final Analysis Complete
