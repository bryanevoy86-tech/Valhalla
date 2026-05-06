# MILLION-PATH: Canonical Strategy Layer

**Status:** FOUNDATIONAL DESIGN  
**Purpose:** Define all possible deal strategies for scale operations  
**Timeline:** Day-one through enterprise scale  
**Last Updated:** 2026-04-13  

---

## PHILOSOPHY

A "strategy" is the exit plan. It defines how we make money from an opportunity:
- **WHOLESALE:** Buy low, sell to another investor, close in days, profit on spread
- **HOLD:** Buy, rent out, hold for appreciation, profit on cash flow + growth
- **FLIP:** Buy, renovate, sell retail, profit on margin
- **PARTNERSHIP:** Co-own with buyer, profit on equity share

These are the only four we need for launch. More strategies unlock later.

---

## LAUNCH-READY STRATEGIES (Day 1)

### Strategy 1: WHOLESALE

**Definition:** Buy from seller, immediately sell to another investor (buyer), profit on spread

**How We Profit:**
- Purchase price: $250k (from seller)
- Sale price: $290k (to buyer/investor)
- Profit: $40k (spread)

**Timeline:** 7-30 days (fast close)

**Who Owns:** Wholesale team leader

**Key Tasks:**
1. Find seller below-market-rate property
2. Negotiate favorable terms
3. Find buyer willing to pay spread
4. Close simultaneously (or back-to-back)
5. Collect spread

**Required Data at INTAKE_PROCESSED:**
```json
{
  "strategy": "wholesale",
  "purchase_price_target": 250000,
  "after_repair_value_estimate": 300000,
  "estimated_repairs": 5000,
  "wholesale_buyer_target_price": 280000,
  "estimated_spread": 30000
}
```

**Deal Viability Check:**
- spread ≥ 20% of purchase price → VIABLE
- spread ≥ $15k → VIABLE
- spread < 10% → MARGINAL
- spread < $5k → DEAD (too thin)

**Risk Factors:**
- Buyer not found by close date
- Seller backs out
- Buyer inspects and demands repair credits
- Lender appraises low

**Supported By (Current Routes):**
- ✅ POST /execution/intake (capture opportunity)
- ✅ POST /execution/intake/{id}/process (classify as wholesale)
- ❓ GET /buyer endpoints (buyer matching - may exist)
- ❓ GET /portfolio endpoints (track completed wholesales)

**Day-One Workflow:**
```
1. Parse property text → Estimate ARV, repairs
2. Calculate spread (MLS comparables, repair quotes)
3. Classify as WHOLESALE if spread viable
4. Queue "Find buyer" task
5. Manual wholesaler finds matching buyer
6. Close when buyer found
```

**Post-Launch Enhancements:**
- Auto-match to registered wholesalers
- Auto-notify wholesalers of available spread
- Buyer registry integration
- Contract template pre-fill

---

### Strategy 2: HOLD

**Definition:** Buy property, rent it out long-term, profit on cash flow + appreciation

**How We Profit:**
- If rental market: +$800/month cash flow × 12 months = +$9.6k/year
- If appreciation: +$10k/year on 5% appreciation
- Tax benefits: Depreciation, mortgage interest deduction
- Total annual profit: +$15-25k/year

**Timeline:** 5+ years (long-term commitment)

**Who Owns:** Portfolio manager / Asset manager

**Key Tasks:**
1. Acquire property favorable to rental market
2. Obtain appropriate financing (rental-grade loan)
3. List/show property to tenants
4. Manage tenant relationship
5. Track cash flow
6. Monitor property value
7. Decide on exit (sell in 5-10 years)

**Required Data at INTAKE_PROCESSED:**
```json
{
  "strategy": "hold",
  "purchase_price": 250000,
  "estimated_monthly_rent": 2000,
  "estimated_expenses_monthly": 800, // taxes, insurance, maintenance
  "estimated_net_monthly_cashflow": 1200,
  "expected_annual_appreciation": 0.05,
  "management_level": "hands-on|property_manager|full_service",
  "financing_available": true
}
```

**Deal Viability Check:**
- Monthly cash flow (rent - expenses) > $500 → VIABLE
- Cap rate (annual profit / price) > 5% → VIABLE
- Cap rate > 8% → STRONG
- Cap rate < 3% or negative → DEAD
- Can finance? → essential

**Risk Factors:**
- Tenant turnover / vacancy
- Unexpected major repairs
- Market downturn (value drop)
- Property tax increase
- Insurance rate spikes
- Landlord legislation changes

**Supported By (Current Routes):**
- ✅ POST /execution/intake
- ✅ POST /execution/intake/{id}/process
- ❓ /portfolio endpoints (tracking)
- ❓ /holdings endpoints (might exist already)

**Day-One Workflow:**
```
1. Parse property text → Estimate rental market
2. Calculate monthly cash flow (rent - taxes - insurance - maintenance)
3. Calculate cap rate
4. Classify as HOLD if cap rate > 5%
5. Queue "Verify rental market" task
6. Manual operator confirms rental viability
7. Operators decide (own vs pass)
```

**Post-Launch Enhancements:**
- Zillow/Trulia rental comp integration
- Tenant registry lookup
- Property management company recommendations
- Cash flow projection models
- Tax benefit calculator

---

### Strategy 3: FLIP (Renovation)

**Definition:** Buy undervalued property, renovate it, sell retail, profit on margin

**How We Profit:**
- Purchase price: $200k (distressed property)
- Repairs: $40k (comprehensive renovation)
- Total invested: $240k
- Retail sale price: $320k (market rate for renovated property)
- Profit: $80k

**Timeline:** 4-6 months (renovation period)

**Who Owns:** Construction manager / Flip coordinator

**Key Tasks:**
1. Find distressed/undervalued property
2. Estimate accurate repair scope
3. Arrange financing (fix-and-flip loan)
4. Coordinate contractors and subcontractors
5. Manage renovation timeline and budget
6. List for retail sale
7. Close with retail buyer

**Required Data at INTAKE_PROCESSED:**
```json
{
  "strategy": "flip",
  "purchase_price": 200000,
  "estimated_repair_cost": 40000,
  "estimated_after_repair_value": 320000,
  "estimated_profit_before_holding_costs": 80000,
  "estimated_holding_period_months": 6,
  "construction_complexity": "cosmetic|moderate|major",
  "contractor_availability": true
}
```

**Deal Viability Check:**
- (ARV - purchase - repairs - holding costs - realtor fees) / purchase > 20% → VIABLE
- Profit margin > $50k → VIABLE
- Profit margin < $20k → MARGINAL (too risky for time)
- Repair costs > 40% of purchase → DEAD (better just to hold as-is)

**Risk Factors:**
- Construction delays (weather, supply chain)
- Repair costs exceed estimates
- Hidden issues found during renovation
- Market downturn during renovation
- Contractor quality issues
- Retail buyer takedown delays

**Supported By (Current Routes):**
- ✅ POST /execution/intake
- ✅ POST /execution/intake/{id}/process
- ❓ /brrrr endpoints (Buy, Rehab, Rent, Refinance - related strategy)

**Day-One Workflow:**
```
1. Parse property specs → Estimate repairs needed
2. Get contractor quotes (or use historical data)
3. Calculate margin (ARV - purchase - repairs - costs)
4. Classify as FLIP if margin viable
5. Queue "Get detailed inspection" task
6. Queue "Confirm contractor availability" task
7. Manual operator decides (commit to flip or pass)
```

**Post-Launch Enhancements:**
- Contractor registry lookup
- Historical repair cost database
- Supply chain risk tracking
- Project management integration
- Real-time renovation timeline tracking

---

### Strategy 4: PARTNERSHIP

**Definition:** Co-own property with buyer/investor, split equity/profit

**How We Profit:**
- Our equity stake: 20-50% of property value
- Buyer's equity stake: 50-80%
- We profit when buyer sells or refinances (realize equity)
- We may also get management fees
- Exit: Sell property in 3-5 years, split proceeds

**Timeline:** 3-10 years (depends on partner exit plan)

**Who Owns:** Partnership manager / Investor relations

**Key Tasks:**
1. Identify property suitable for partnership
2. Find qualified partner/buyer willing to co-own
3. Negotiate equity split and management roles
4. Document partnership agreement
5. Manage partner relationship
6. Track partner performance
7. Plan exit (joint sale, buy partner out, or partner buys us out)

**Required Data at INTAKE_PROCESSED:**
```json
{
  "strategy": "partnership",
  "purchase_price": 300000,
  "our_proposed_equity_stake": 0.30,
  "partner_proposed_equity_stake": 0.70,
  "partnership_structure": "llc|joint_venture|equity_share",
  "partner_role": "capital_only|active_management|co_management",
  "projected_annual_return": 0.12,
  "exit_plan": "joint_sale|buy_partner_out|partner_buys_us"
}
```

**Deal Viability Check:**
- Partner has capital / track record → VIABLE
- Our equity stake ≥ 15% → VIABLE
- Our equity stake > $50k → VIABLE
- No qualified partner found → DEAD (convert to hold or pass)
- Partner equity > 80% → MARGINAL (we lose control)

**Risk Factors:**
- Partner mismanagement
- Partner defaults on obligations
- Partnership dispute / litigation
- Market downturn affects equity value
- Partner wants out early (forces sale)
- Communication breakdown

**Supported By (Current Routes):**
- ✅ POST /execution/intake
- ✅ POST /execution/intake/{id}/process
- ❓ /investor endpoints (partner registry)

**Day-One Workflow:**
```
1. Parse property → suitable for partnership?
2. Identify potential partners from network
3. Model equity splits and returns
4. Classify as PARTNERSHIP if partner identified
5. Queue "Verify partner capability" task
6. Queue "Draft partnership agreement" task
7. Manual operator negotiates with partner
```

**Post-Launch Enhancements:**
- Partner registry with track records
- Standard partnership agreements (template library)
- Equity split modeling tools
- Performance tracking dashboards
- Automatic distribution calculations

---

## FUTURE STRATEGIES (Year 2+)

These strategies unlock after we've proven the core four and built supporting infrastructure.

### Strategy 5: COMMERCIAL (Year 2)
**Definition:** Acquire commercial properties (retail, office, industrial)  
**Requires:** Commercial underwriting, different financing, commercial broker network

### Strategy 6: CREATIVE FINANCE (Year 2)
**Definition:** Seller financing, subject-to, lease-option, contract for deed  
**Requires:** Legal review team, alternative financing modeling

### Strategy 7: DEVELOPMENT (Year 2+)
**Definition:** Land development or construction from ground up  
**Requires:** Construction expertise, design/architect network, development accounting

### Strategy 8: ARBITRAGE (Year 2+)
**Definition:** Market arbitrage, zone-based pricing differences  
**Requires:** Multi-zone pricing database, cross-zone buyer network

### Strategy 9: ACQUISITION FOR EQUITY (Year 2+)
**Definition:** Acquire partner's portfolio for equity stake in merged entity  
**Requires:** Portfolio analysis, valuation, M&A considerations

---

## STRATEGY SELECTION LOGIC (Day 1)

When system receives opportunity, it must classify into one of the four strategies:

```
IF property_type NOT IN {sfh, multifamily, small_commercial}:
  → DEAD (too complex for day-one)

ELSE IF margin_percentage > 20% AND spread > $15k:
  → PRIMARY: WHOLESALE (quick profit)
  → SECONDARY: FLIP (if time available)

ELSE IF rental_cashflow_positive AND cap_rate > 5%:
  → PRIMARY: HOLD (recurring profit)
  → SECONDARY: PARTNERSHIP (bring in investor for capital)

ELSE IF can_renovate AND post_repair_margin > 25%:
  → PRIMARY: FLIP (renovation profit)
  → SECONDARY: HOLD (if market weak)

ELSE IF can_find_partner AND equity_stake > 15%:
  → PRIMARY: PARTNERSHIP (leverage partner capital)

ELSE:
  → DEAD (no viable strategy)
```

**Current Implementation:**
- Live system classifies as "real_estate" (generic)
- No specific strategy selection yet
- Ready to add post-WeWeb

---

## STRATEGY IN CASE RECORD

```json
{
  "case_id": 3,
  "strategy": "wholesale",  // which strategy
  "strategy_confidence": 0.92,  // how confident is system
  "strategy_alternatives": ["flip", "hold"],  // other viable options
  "strategy_data": {
    "wholesale": {
      "estimated_spread": 40000,
      "buyer_profile_target": "contractor_investor"
    },
    "flip": {
      "estimated_profit": 35000,
      "timeline_months": 5
    },
    "hold": {
      "estimated_cashflow_annual": 9600,
      "cap_rate": 0.048
    }
  }
}
```

---

## STRATEGY IN API RESPONSES

**GET /execution/cases/{case_id}** should return:
```json
{
  "case_id": 3,
  "strategy": "wholesale",
  "strategy_details": {
    "type": "wholesale",
    "spread": 40000,
    "buyer_needed": true
  }
}
```

**GET /execution/cases/{case_id}/tasks** should categorize by strategy:
```json
{
  "strategy": "wholesale",
  "strategy_tasks": [
    "Find wholesale buyer",
    "Negotiate buyer terms",
    "Coordinate back-to-back close"
  ],
  "common_tasks": [
    "Verify property",
    "Contact seller"
  ]
}
```

---

## STRATEGY DATA MODEL

All strategies link to common fields:

```sql
CREATE TABLE strategy_profiles (
  strategy_id UUID PRIMARY KEY,
  strategy_name VARCHAR(50),  -- wholesale, hold, flip, partnership
  strategy_key VARCHAR(20),  -- WHOLESALE, HOLD, FLIP, PARTNER
  description TEXT,
  min_margin_dollars INT,  -- $5k for wholesale, $20k for flip
  min_margin_percent FLOAT,  -- 10% for wholesale, 25% for flip
  typical_timeline_days INT,  -- 14 for wholesale, 180 for flip
  primary_owner_role VARCHAR(50),  -- who leads this?
  requires_financing BOOLEAN,
  risk_level VARCHAR(20),  -- low, medium, high
  is_active BOOLEAN,
  created_at TIMESTAMP
);
```

---

## WEWEB DISPLAY

First WeWeb build should show strategy as:

```
Strategy: WHOLESALE
├─ Estimated Spread: $40,000 ✓
├─ Timeline: 14 days
├─ Next: Find Buyer

Alternative Strategies:
  • FLIP: $35,000 profit (5 months)
  • HOLD: $9,600 annual cash flow
```

---

## SAFE TO APPLY NOW

**Constants Only (No Breaking Changes):**

Can create `app/constants/strategies.py`:

```python
STRATEGIES = {
    "WHOLESALE": {
        "key": "wholesale",
        "name": "Wholesale",
        "description": "Buy low, sell to investor quickly",
        "min_spread_percent": 0.10,
        "min_spread_dollars": 5000,
        "typical_days": 14,
        "owner_role": "wholesome_team",
    },
    "HOLD": {
        "key": "hold",
        "name": "Hold for Cash Flow",
        "description": "Rent out, collect cash flow",
        "min_cap_rate": 0.05,
        "typical_years": 5,
        "owner_role": "portfolio_manager",
    },
    "FLIP": {
        "key": "flip",
        "name": "Flip / Renovate",
        "description": "Renovate and sell retail",
        "min_profit_percent": 0.25,
        "min_profit_dollars": 20000,
        "typical_days": 180,
        "owner_role": "construction_manager",
    },
    "PARTNERSHIP": {
        "key": "partnership",
        "name": "Partnership",
        "description": "Co-own with investor partner",
        "min_our_equity_percent": 0.15,
        "min_our_equity_dollars": 50000,
        "typical_years": 5,
        "owner_role": "partnership_manager",
    },
}

STRATEGY_LIST = list(STRATEGIES.keys())
```

**Risk Level:** ZERO (constants only, no DB changes)

---

## APPLICATION TIMELINE

### NOW (Week of 2026-04-15)
- ✅ Create constants/strategies.py
- ✅ Deploy as documentation
- ✅ No WeWeb build changes yet

### POST-WEWEB LAUNCH (Week of 2026-04-22)
- ⏳ Update POST /execution/intake/{id}/process to classify strategy
- ⏳ Add strategy field to response
- ⏳ Update GET /execution/cases/{id} to return strategy
- ⏳ WeWeb displays strategy in case summary

### WEEK 2 POST-LAUNCH
- ⏳ Implement strategy-specific task generation
- ⏳ Queue strategy-appropriate tasks
- ⏳ Show strategy alternatives

### MONTH 2
- ⏳ Add buyer matching for wholesale
- ⏳ Add partner registry lookup
- ⏳ Auto-route by strategy

---

## MIGRATION SAFETY CHECKLIST

- [x] All strategies are additive (no breaking changes to existing data)
- [x] Constants deployment has zero risk
- [x] Database schema changes (if any) are post-launch
- [x] Existing cases can run without strategy field
- [x] No required fields added to live tables
- [x] Backward compatible with current API

---

## NEXT STEPS

1. Review strategy definitions with team
2. Validate profitability thresholds with historical deals
3. Deploy constants file to production
4. Test strategy classification logic offline
5. Integrate into POST /execution/intake/{id}/process response

---

**Document Owner:** Strategy Architecture Team  
**Status:** CANONICAL - Ready for implementation  
**Last Updated:** 2026-04-13  
**Next Review:** Pre-WeWeb launch  
