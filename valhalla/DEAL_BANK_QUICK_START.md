# Deal Bank Quick Start (DB-1 through DB-5)

## Files Created

```
backend/app/core_gov/deals/
  ├── __init__.py
  ├── models.py (DealIn, Deal)
  ├── store.py (CRUD)
  ├── router.py (4 endpoints)
  ├── seed/
  │   ├── __init__.py
  │   ├── generator.py
  │   └── router.py
  ├── scoring/
  │   ├── __init__.py
  │   ├── service.py
  │   └── router.py
  └── next_action/
      ├── __init__.py
      ├── service.py
      └── router.py
```

## Core Endpoints

### Create Deal
```bash
curl -X POST http://localhost:8000/core/deals \
  -H "Content-Type: application/json" \
  -d '{
    "country": "CA",
    "province_state": "ON",
    "city": "Toronto",
    "strategy": "wholesale",
    "property_type": "sfh",
    "arv": 450000,
    "asking_price": 380000,
    "est_repairs": 25000,
    "seller_motivation": "high",
    "stage": "new",
    "lead_source": "real"
  }'
```

### List Deals
```bash
curl "http://localhost:8000/core/deals?limit=10&stage=qualified&source=seed"
```

### Generate 200 Seed Deals
```bash
curl -X POST "http://localhost:8000/core/deals/seed/generate?n=200&ca_ratio=0.5"
```

### Score a Deal
```bash
curl "http://localhost:8000/core/deals/{deal_id}/score"
```

### Get Next Action (Cone-Aware)
```bash
curl "http://localhost:8000/core/deals/{deal_id}/next_action"
```

### Update Deal
```bash
curl -X PATCH "http://localhost:8000/core/deals/{deal_id}" \
  -H "Content-Type: application/json" \
  -d '{"stage": "contacted", "notes": "Called seller, interested in hearing details."}'
```

## Seed Geography

**Canada (16 cities):**  
BC: Vancouver, Surrey, Kelowna  
AB: Calgary, Edmonton  
MB: Winnipeg  
SK: Regina, Saskatoon  
ON: Toronto, Mississauga, Ottawa, Hamilton  
QC: Montreal, Quebec City  
NS: Halifax  

**USA (9 cities):**  
FL: Orlando, Tampa, Jacksonville, Miami  
TX: Dallas, Houston  
GA: Atlanta  
NC: Charlotte  
SC: Charleston  

## Score Interpretation

- **0–40:** Pass on deal (limited equity, high repairs, low motivation)
- **40–60:** Monitor (potential with improvements)
- **60–80:** Pursue (good opportunity, Cone band permitting)
- **80–100:** Prioritize (excellent opportunity, contact immediately if Cone A/B)

**Flags to Check:**
- `missing_arv`: ARV not provided (estimate or skip)
- `missing_asking`: Asking price missing
- `low_equity`: <15% equity after repairs
- `heavy_repairs`: >25% of ARV

## Cone Band Behavior

- **Bands A/B (Normal/Caution):** "Call now", "Text then call", "Send offer", "Negotiate"
- **Bands C/D (Stabilization):** "Light contact", "Follow up light", "Hold"

Use next_action endpoint to get Cone-aware recommendation without hardcoding logic.

---

**Status:** ✅ Production ready. Wire into Heimdall's Go decision system.
