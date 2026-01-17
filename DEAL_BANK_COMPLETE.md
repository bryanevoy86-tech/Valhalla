# Deal Bank System (DB-0 through DB-5) — Complete Implementation

**Status:** ✅ COMPLETE  
**Files Created:** 13 (10 Python, 3 __init__.py)  
**Routers Wired:** 4 (deals, seed, scoring, next_action)  
**Endpoints:** 9  
**Lines of Code:** ~450

---

## Overview

**Deal Bank** is the durable deal pipeline substrate for Heimdall's AI/Human hybrid operation. It provides:

- **DB-1 (Deal Model + Store):** DealIn/Deal Pydantic models with file-backed CRUD (deals.json, 20K cap)
- **DB-2 (Deal Router):** POST /, GET /, GET /{id}, PATCH /{id} endpoints with audit trail
- **DB-3 (Seed Generator):** generate_seed_batch() with 16 CA cities + 9 USA cities, 200 deal default, configurable CA/US ratio
- **DB-4 (Scoring v1):** score_deal() with equity %, motivation, repairs, stage analysis, flags, MAO suggestions
- **DB-5 (Next Action):** next_action_for_deal() with Cone band awareness (A/B normal vs C/D stabilization)

---

## Architecture

### Deal Model (DB-1)

```python
class Deal(BaseModel):
    # identity
    id: str  # UUID
    country: str  # CA or US
    province_state: str
    city: str
    address: Optional[str]
    postal_zip: Optional[str]

    # deal type
    strategy: str  # wholesale|brrrr|flip|rental
    property_type: str  # sfh|duplex|triplex|fourplex|condo|townhouse|land|small_mf
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    sqft: Optional[int]

    # financials (country currency)
    arv: Optional[float]  # After Repair Value
    asking_price: Optional[float]
    est_repairs: Optional[float]
    mao: Optional[float]  # Max Allowable Offer (calculated by scoring)
    est_rent_monthly: Optional[float]  # For BRRRR/rental

    # seller / motivation
    seller_motivation: str  # high|medium|low|unknown
    seller_reason: Optional[str]  # inherited, tired_landlord, job_loss, divorce, etc.
    timeline_days: Optional[int]

    # pipeline
    stage: str  # new|contacted|qualified|offer_sent|negotiating|under_contract|dead|closed
    lead_source: str  # seed|public|real
    tags: List[str]  # e.g., ["wholesale", "ca", "on"]
    notes: Optional[str]

    # timestamps
    created_at_utc: str  # ISO 8601
    updated_at_utc: str

    # arbitrary metadata
    meta: Dict[str, Any]
```

### File Storage

**Location:** `data/deals.json`  
**Format:** `{"items": [deal1, deal2, ...]}`  
**Cap:** 20,000 items (auto-trim to last 20K on overflow)

### CRUD Operations (DB-1 Store)

```python
add_deal(payload: dict) -> dict  # Create, return with id + timestamps
get_deal(deal_id: str) -> dict | None
update_deal(deal_id: str, patch: dict) -> dict | None
list_deals(limit=50, stage=None, source=None) -> list[dict]  # Newest first
```

### Deal Router Endpoints (DB-2)

| Method | Endpoint | Payload | Response |
|--------|----------|---------|----------|
| POST | `/core/deals` | DealIn | Deal (with id, timestamps) |
| GET | `/core/deals` | ?limit=50&stage=&source= | {"items": [deals]} |
| GET | `/core/deals/{deal_id}` | — | Deal |
| PATCH | `/core/deals/{deal_id}` | DealPatch | Deal (updated) |

**DealPatch Fields:** stage, notes, tags, mao, arv, asking_price, est_repairs, meta

### Seed Generator (DB-3)

**Function:** `generate_seed_batch(n=200, ca_ratio=0.5) -> list[dict]`

**Canadian Cities (16):** Vancouver, Surrey, Kelowna, Calgary, Edmonton, Winnipeg, Regina, Saskatoon, Toronto, Mississauga, Ottawa, Hamilton, Montreal, Quebec City, Halifax

**USA Cities (9):** Orlando, Tampa, Jacksonville, Miami, Dallas, Houston, Atlanta, Charlotte, Charleston

**Configuration:**
- n: Number of deals to generate (default 200)
- ca_ratio: Fraction of Canadian deals (0.5 = 50% CA, 50% US)

**Realistic Ranges:**
- CA ARV: $220K–$950K
- USA ARV: $150K–$800K
- Repairs: 10–25% of ARV
- Motivation: 45% high, 40% medium, 15% low
- Stages: 35% new, 25% contacted, 20% qualified, 10% offer_sent, 10% negotiating

**Seed Endpoint:**

```
POST /core/deals/seed/generate?n=200&ca_ratio=0.5
→ {"ok": true, "created": 200}
```

### Scoring Service (DB-4)

**Function:** `score_deal(deal: dict) -> dict`

**Output:**
```python
{
    "score": 0–100,
    "equity_pct": 0–100.0,
    "mao_suggested": float,
    "flags": list[str],  # e.g., ["missing_arv", "low_equity", "heavy_repairs"]
}
```

**Scoring Logic:**
- **Base:** 50
- **Motivation:** +15 (high), +7 (medium), -5 (low)
- **Equity:** +20 (≥35%), +12 (≥25%), +5 (≥15%), -8 (< 15%, flag)
- **Repairs:** -8 (≥25% of ARV, flag), -4 (≥15%)
- **Stage:** +5 (qualified, offer_sent, negotiating)
- **MAO heuristic by strategy:**
  - Wholesale: (ARV × 0.70) – Repairs
  - Flip: (ARV × 0.75) – Repairs
  - BRRRR/Rental: (ARV × 0.80) – Repairs
- **Clamp:** 0–100

**Flags:** missing_arv, missing_asking, repairs_negative, low_equity, heavy_repairs

**Scoring Endpoint:**

```
GET /core/deals/{deal_id}/score
→ {"deal_id": "...", "score": {"score": 72, "equity_pct": 28.5, "mao_suggested": 145000.00, "flags": []}}
```

### Next Action Service (DB-5)

**Function:** `next_action_for_deal(deal: dict) -> dict`

**Cone Band Awareness:**

- **Bands C/D (Stabilization/Survival):** Minimal contact, protect pipeline
  - new → `light_contact` (medium priority)
  - contacted/qualified → `follow_up_light` (medium priority)
  - else → `hold` (low priority)

- **Bands A/B (Expansion/Caution):** Scale outreach, qualify, offer, negotiate
  - new: high score → `call_now` (high), else → `text_then_call` (medium)
  - contacted → `qualify` (high/medium based on score)
  - qualified → `send_offer` (high)
  - offer_sent → `follow_up_24h` (high/medium based on score)
  - negotiating → `negotiate` (high)
  - else → `review` (low)

**Next Action Endpoint:**

```
GET /core/deals/{deal_id}/next_action
→ {"deal_id": "...", "next": {"band": "A", "action": "call_now", "why": "High score new lead. Contact immediately.", "priority": "high"}}
```

---

## Integration Points

### Core Router Wiring

All 4 routers included in `core_router.py`:

```python
from .deals.router import router as deals_router
from .deals.seed.router import router as deals_seed_router
from .deals.scoring.router import router as deals_score_router
from .deals.next_action.router import router as deals_next_action_router

core.include_router(deals_router)
core.include_router(deals_seed_router)
core.include_router(deals_score_router)
core.include_router(deals_next_action_router)
```

### Audit Trail Integration

- `DEAL_CREATED`: New deal created with strategy + source
- `DEAL_UPDATED`: Existing deal patched
- `DEALS_SEED_GENERATED`: Batch seed generation with CA ratio

### Cone Band Awareness (DB-5)

Reads from `get_cone_state()` to determine stabilization vs expansion mode.

---

## End-to-End Workflow

```bash
# 1. Generate 200 seed deals (50% CA, 50% US)
curl -X POST "http://localhost:8000/core/deals/seed/generate?n=200&ca_ratio=0.5"
# → {"ok": true, "created": 200}

# 2. List recent deals
curl "http://localhost:8000/core/deals?limit=5"
# → {"items": [deal1, deal2, deal3, deal4, deal5]}

# 3. Copy deal_id from response
DEAL_ID="<uuid-from-step-2>"

# 4. Score the deal
curl "http://localhost:8000/core/deals/$DEAL_ID/score"
# → {"deal_id": "...", "score": {"score": 72, "equity_pct": 28.5, "mao_suggested": 145000.0, "flags": []}}

# 5. Get recommended next action (depends on Cone band)
curl "http://localhost:8000/core/deals/$DEAL_ID/next_action"
# → {"deal_id": "...", "next": {"band": "A", "action": "call_now", "why": "High score new lead. Contact immediately.", "priority": "high"}}

# 6. Patch deal (move to contacted, add notes)
curl -X PATCH "http://localhost:8000/core/deals/$DEAL_ID" \
  -H "Content-Type: application/json" \
  -d '{"stage": "contacted", "notes": "Voicemail left, callback expected Friday"}'
# → Deal (with updated stage, updated_at_utc)

# 7. Check next action again (should recommend qualify or follow_up_light based on Cone)
curl "http://localhost:8000/core/deals/$DEAL_ID/next_action"
# → Updated action based on new stage
```

---

## Data Directories

- `data/deals.json` — All deals (auto-created on first POST)
- `data/exports/` — Ready for integration with export pipeline

---

## Testing Checklist

- ✅ POST /core/deals (create single deal)
- ✅ POST /core/deals/seed/generate (batch creation)
- ✅ GET /core/deals (list with filters)
- ✅ GET /core/deals/{id} (single get)
- ✅ PATCH /core/deals/{id} (update)
- ✅ GET /core/deals/{id}/score (scoring)
- ✅ GET /core/deals/{id}/next_action (next action)
- ✅ Audit trail events logged
- ✅ File cap respected (20K)
- ✅ Cone band awareness works

---

## Summary

**DB-0 through DB-5** provide a complete durable deal pipeline substrate:

1. **Persistent storage** (JSON file-backed, 20K cap)
2. **Flexible CRUD** with filtering by stage/source
3. **Seed generation** with realistic Canada/US geographic distribution
4. **Intelligent scoring** (0–100) with equity, motivation, repairs analysis
5. **Cone-aware next actions** (stabilization vs expansion behavior)
6. **Audit trail** integration with all governance events

**Ready for:** Direct dealer integration, public/real deal ingestion, Heimdall scoring/recommendations before Go decision.
