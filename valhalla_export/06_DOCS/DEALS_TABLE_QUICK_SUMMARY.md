# Deals Table Quick Reference - March 30, 2026

## ONE-PAGE SUMMARY

### The Core Answer

**Q: Is pack_62's deals table THE production table?**  
**A: YES - It's the only one that exists on Render.**

---

## The Three Table Definitions

| Property | pack_62_underwriter | Pipeline (20260305) | Bootstrap |
|----------|-------------------|-------------------|-----------|
| **Location** | services/api/alembic/versions/ | alembic/versions/ | db_bootstrap.py |
| **Revision ID** | pack_62_underwriter | f2b00b1c2d4c | N/A (direct SQL) |
| **Created** | Unknown (pack system) | 2026-03-05 | When needed |
| **Exists?** | ✅ Yes (Production) | ❌ No (IF NOT EXISTS skipped) | ✅ Dev only |
| **Schema Focus** | Underwriter/Geo | Lead Pipeline | Lead Pipeline |
| **Key ID Column** | BigInteger id | Integer id | Integer id |
| **Lead Relationship** | ❌ Uses ext_id | ✅ lead_id FK | ✅ lead_id FK |
| **Core Fields** | ext_id, address, city, postal_code, lat, lng, ask_price, status, meta | lead_id, title, stage, arv, estimated_repair_cost, max_allowable_offer | lead_id, title, stage, arv, estimated_repair_cost, max_allowable_offer |

---

## Schema Comparison

### pack_62 Columns (What Exists on Render)
```
id (BigInt)
ext_id (String)
created_ts (DateTime)
address city province postal_code (geo fields)
lat lng (coordinates)
status (String)
ask_price (Numeric)
notes (Text)
meta (JSONB)
+ recently added: lead_id, updated_ts
```

### Pipeline Columns (What ORM Expects)
```
id (Integer)
created_ts updated_ts (DateTime)
lead_id (FK→leads)
title (String)
stage status (String)
arv estimated_repair_cost (Numeric)
max_allowable_offer target_assignment_fee (Numeric)
score (Numeric)
notes (Text)
disposition_status (String)
```

### Currently Missing from pack_62
- ❌ title
- ❌ arv, estimated_repair_cost, max_allowable_offer, target_assignment_fee
- ❌ disposition_status
- ❌ (but recently added: lead_id, updated_ts)

---

## Timeline

```
1. pack_62_underwriter migration
   ↓ Creates deals table (underwriter schema)
   ├─ Creates: comps, underwriting_signals, deal_scores
   ├─ All dependent packs (63, 64, 65) reference this table
   ↓
2. 2026-03-05: create_core_pipeline_tables tries to create
   ├─ Uses IF NOT EXISTS → SKIPPED (pack_62 already exists)
   ├─ Never creates pipeline version
   ↓
3. 2026-03-30: Patches applied to pack_62 table
   ├─ Add updated_ts column
   ├─ Add lead_id column
   ↓ Result: GET /api/deals may work now (basic queries)
```

---

## The Real Problem

**Two teams, one table name, incompatible schemas:**

- **Underwriter Team (pack_62)**: "We need geolocation, external system IDs, deal scoring"
- **Pipeline Team (20260305)**: "We need lead tracking, deal valuation, offer workflow"
- **Result**: Schema warfare, patches, technical debt

---

## Current State (2026-03-30)

### Production Database (Render)
```
✅ deals table EXISTS (pack_62)
├─ Some columns from both schemas (after patches)
├─ lead_id added (column, no data)
├─ updated_ts added
└─ ⚠️ Missing: Some pipeline fields (title, arv, etc.)
```

### API Status
- 🔄 GET /api/deals: Likely working (patched)
- ⚠️ Data completeness: Partial (schema mismatch)
- ⚠️ Sustainability: Questionable (technical debt)

---

## Migration Dependency Chain

```
Production Path:
  pack_61 → pack_62 [CREATES deals] → pack_63 → pack_64 → pack_65 → ... → patches

Root Pipeline Path (unused):
  20260305 [IF NOT EXISTS → skips] 
  
Bootstrap Path:
  db_bootstrap.py [Fresh dev DB only]
```

---

## Bottom Line

1. **pack_62 IS the production deals table**
2. **It was created by Pack 62 Underwriter migration**
3. **Pipeline table (20260305) never runs due to IF NOT EXISTS**
4. **Bootstrap table only for fresh dev databases**
5. **Recent patches add missing columns to pack_62 to bridge gap**
6. **Schema mismatch is architectural, not a bug**

---

## Files to Know

| What | Where |
|------|-------|
| Production table creates | services/api/alembic/versions/pack_62_underwriter.py |
| Pipeline table attempts | alembic/versions/20260305_000000_create_core_pipeline_tables.py |
| ORM model expects | services/api/app/deals/models.py |
| Patches applied | services/api/alembic/versions/20260330_add_*.py |
| Full analysis | DEALS_TABLE_ANALYSIS_20260330.md |

---

**Status**: Investigation Complete  
**Confidence**: High  
**Date**: March 30, 2026
