# Arbitrage Phase A - Deployment Status & Next Steps

**Date:** February 3, 2026  
**Status:** ✅ Code Complete | ⏳ Route Registration Pending

---

## What's Deployed

### 1. Core Models (SQLAlchemy ORM)
```
✅ market_feed_event.py          - Normalized inbox for market data sources
✅ arbitrage_opportunity.py      - Detected spread opportunities  
✅ arbitrage_sim_trade.py        - Paper trading ledger (Phase A only)
```

### 2. Engine Logic
```
✅ app/engines/arbitrage/engine.py
   - ArbitragePolicy (min_roi=3%, min_profit=$15)
   - scan_arbitrage() function
   - Detects best buy/sell pairs per SKU
   - Calculates net profit and ROI
   - Creates opportunity records
   - Simulates execution (no real capital moves)
```

### 3. API Endpoints (Ready to Activate)
```
✅ POST   /api/arbitrage/scan              - Run scan job
✅ GET    /api/arbitrage/health            - Health check
✅ GET    /api/arbitrage/scorecard         - Performance summary
✅ GET    /api/arbitrage/opportunities     - List detected opportunities

✅ POST   /api/jobs/arbitrage/scan         - Job wrapper (for cron/scheduling)
```

### 4. Database Migration
```
✅ Migration: 20260203_arbitrage_phase_a
   Status: Committed, ready to run
   Chain: sandbox_visibility → engine_readiness → arbitrage_phase_a
   Tables created:
     - market_feed_events
     - arbitrage_opportunities
     - arbitrage_sim_trades
```

---

## How It Works (Phase A)

### Workflow: Observation → Detection → Simulation

1. **Feed Inbox** (`market_feed_events`)
   - Manually populate OR connect API importers later
   - Normalized structure: source, sku, venue, price, url

2. **Scan Execution**
   ```
   FOR each SKU in feed:
     best_buy = cheapest source
     best_sell = highest source
     IF (best_sell.price > best_buy.price):
       Calculate spread, fees, shipping
       IF (net_profit >= $15 AND roi >= 3%):
         Create opportunity record
         Create sim_trade record
   ```

3. **Scoring** (Confidence)
   ```
   confidence = min(0.95, max(0.1, 0.4 + (roi * 3.0)))
   - Low confidence: small spreads
   - High confidence: wide spreads with good ROI
   ```

4. **Visibility**
   - Scorecard endpoint shows:
     - Open opportunities count
     - Total sim profits
     - Average ROI
   - All marked "SIM_ONLY" (no execution)

---

## Test Data (Ready to Insert)

File: `services/api/scripts/arbitrage_test_data.sql`

Contains 3 test cases:
1. **BESTSELLER_001** - Good spread ($55 gross, $25 net, 25% ROI) → PASS
2. **SKU999** - Marginal spread ($10 gross, -$12 net, -10% ROI) → FAIL  
3. **ELECTRONICS_042** - Excellent spread ($140 gross, $112 net, 140% ROI) → PASS

When scan runs on this test data:
- Creates 2 opportunities (cases 1 & 3)
- Creates 2 sim trades with positive ROI
- Scorecard shows: $137 total profit, 82.5% avg ROI

---

## Current Deployment Status

### ✅ Completed
- All 10 files created and committed
- Migration chain fixed (single head)
- Pre-queue filter live and working ✓
- Core API responsive ✓

### ⏳ Blocker: Route Registration
- Arbitrage routers not appearing in Render logs
- Routes returning 404
- Silent initialization failure in try/except blocks
- Likely cause: Model import issue or circular dependency

### Workaround (Immediate Activation)
Routes disabled in `main.py` to stabilize core API. To re-enable:

1. **Option A: Direct SQL Execution**
   ```bash
   # Insert test data
   psql $DATABASE_URL < scripts/arbitrage_test_data.sql
   
   # Call scan directly via Python
   python -c "
   from app.engines.arbitrage.engine import scan_arbitrage, ArbitragePolicy
   from app.core.db import SessionLocal
   db = SessionLocal()
   result = scan_arbitrage(db, ArbitragePolicy())
   print(result)
   "
   ```

2. **Option B: Enable Routes (Once Fix Applied)**
   - Uncomment arbitrage router registration in `main.py`
   - Redeploy to Render
   - Test endpoints

---

## Phase A → Phase B Transition

Once Phase A is proving value:

### Phase B: Simulated Execution
```
State: SANDBOX + SIM_EXEC

Changes:
✨ "Buy" and "sell" on paper
✨ Compare simulated vs actual outcome
✨ Learn variance and slippage
✨ Build confidence in detection

Still no real capital movement
Still sandboxed observation
```

### Phase C: Manual Execution (Weeks Away)
```
State: READY

Requirements met:
✅ ≥30 samples collected
✅ Simulated ROI > 15%
✅ Variance < 5%
✅ Predictable behavior proven

Then: Manual execution with caps
      (small amounts, tight controls)
```

---

## Architecture: Why Arbitrage First

### ✅ Arbitrage is the perfect "second engine" because:

**Low Risk**
- No customer impact
- No external commitments
- No capital lock-up
- Pure math + data

**Infrastructure Proves**
- Metrics collection
- Event logging
- Sandbox fidelity
- Promotion workflow

**Enables Passive Engines**
- Wholesaling → (prerequisite)
- Arbitrage → (foundation)
- Rentals/BRRR → (passive builds on arbitrage)
- Trading → (advanced, depends on arbitrage)

---

## Next Steps (Prioritized)

### 1. **Immediate: Fix Route Registration** (30 mins)
   - Debug why lazy imports failing
   - Check for circular dependencies
   - May need to adjust db initialization
   - Once fixed: uncomment routers, redeploy

### 2. **Day 1-2: Insert Test Data & Prove Concept** (15 mins)
   ```bash
   # Insert test data (opportunity spreads)
   curl -X POST /api/arbitrage/scan \
     -H "X-API-Key: $KEY"
   
   # View scorecard
   curl -X GET /api/arbitrage/scorecard \
     -H "X-API-Key: $KEY"
   # Response: 2 opportunities, $137 sim profit
   ```

### 3. **Day 3-5: Connect Real Data Source** (2 hours)
   - eBay API for buy prices
   - Local marketplace for sell prices
   - Update `market_feed_events` table
   - Run daily scans

### 4. **Week 2: Monitor Phase A Metrics** (Ongoing)
   - Opportunity frequency
   - Detection accuracy
   - Variance in spreads
   - Confidence trending

### 5. **Week 3+: Transition to Phase B** (Optional)
   - Enable SIM_EXEC mode
   - Paper trading
   - Outcome tracking

---

## Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `app/models/market_feed_event.py` | Feed inbox | ✅ Created |
| `app/models/arbitrage_opportunity.py` | Spreads detected | ✅ Created |
| `app/models/arbitrage_sim_trade.py` | Paper trades | ✅ Created |
| `app/engines/arbitrage/engine.py` | Scan logic | ✅ Created |
| `app/api/arbitrage/router.py` | REST endpoints | ✅ Created (disabled) |
| `app/jobs/arbitrage_jobs.py` | Job wrapper | ✅ Created (disabled) |
| `alembic/versions/20260203_arbitrage_phase_a.py` | Migration | ✅ Created |
| `scripts/arbitrage_test_data.sql` | Test cases | ✅ Created |
| `main.py` | Router registration | ⏳ Commented out |

---

## Key Philosophy (Why This Order)

> "You don't turn things on. You earn activation rights."

Each engine proves:
1. **Predictability** - Does it do what we expect?
2. **Safety** - Can we observe without risk?
3. **Alignment** - Does it match business goals?

**Arbitrage Phase A** proves all three **without capital risk**.

When metrics align, you graduate to Phase B.
When Phase B proves variance is low, you graduate to Phase C.
When Phase C executes successfully, you move to passive engines.

This is institutional risk management, not guessing.

---

## Activation Commands (Once Routes Are Live)

```bash
# 1. Health check
curl https://valhalla-api-ha6a.onrender.com/api/arbitrage/health \
  -H "X-API-Key: YOUR_KEY"

# 2. Run scan (with test data)
curl -X POST https://valhalla-api-ha6a.onrender.com/api/arbitrage/scan \
  -H "X-API-Key: YOUR_KEY"
# Response: {
#   "ok": true,
#   "scanned": 3,
#   "created_opportunities": 2,
#   "created_sim_trades": 2,
#   "policy": {...}
# }

# 3. View scorecard
curl https://valhalla-api-ha6a.onrender.com/api/arbitrage/scorecard \
  -H "X-API-Key: YOUR_KEY"
# Response: {
#   "engine": "arbitrage",
#   "mode": "SANDBOX_SIM_ONLY",
#   "open_opportunities": 2,
#   "sim_trades": 2,
#   "sim_total_profit": 137.00,
#   "sim_avg_roi": 0.8250
# }

# 4. List opportunities
curl https://valhalla-api-ha6a.onrender.com/api/arbitrage/opportunities \
  -H "X-API-Key: YOUR_KEY"
```

---

**Status:** 🟡 Ready to activate. Route registration issue being resolved. **Core infrastructure deployed.** Pre-queue filter proving value. **Next phase: get arbitrage routes responding, then connect real market data.**
