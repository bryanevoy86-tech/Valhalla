# DATA BOUNDARIES & PHASE 3.1 CONCEPT (Optional)

**Context**: You asked about old asking price, final sold price, repair costs, and market value. Here's the honest boundary.

---

## Current Phase 3: What We Have

| Data | Source | Coverage | Quality | Use Case |
|------|--------|----------|---------|----------|
| **Assessment Value** | Edmonton/Calgary open data | AB properties | High (official) | Primary valuation anchor |
| **Year Built** | Partial (in assessment data) | Not all properties | Medium | Condition proxy |
| **Zoning** | Not in current datasets | AB only | N/A | Regulatory context |
| **Area/Size** | Partial (in assessment data) | Not all properties | Medium | Scale proxy |

---

## Data We DON'T Have (& Why)

### Old Asking Price ❌
- **Why not**: Requires historical MLS data (proprietary, access-controlled)
- **Open alternative**: None reliable
- **Workaround**: Use assessment value as baseline

### Final Sold Price ❌
- **Why not**: MLS sold listings are licensed/restricted
- **Open alternative**: Partial via StatsCan region-level indices
- **Current**: NHPI table (macro context only, not per-property)
- **Workaround**: Use assessment value + conservative markup

### Repair Costs ❌
- **Why not**: Never public; requires expert inspection or contractor quotes
- **Open alternative**: Rule-based estimation (not truth, but defensible)
- **Current approach**: None (we defer to human review)

---

## Honest Boundary: What We CAN Do (Phase 3)

✅ **Assessment Value** (strong anchor)  
✅ **Synthetic Conservative Labels** (safe defaults)  
✅ **Replay Metrics** (accuracy, precision, recall)  
✅ **Human Review Flagging** (>80% flagged by design)

---

## Optional Phase 3.1: Repair Estimator Module

If you want to add **defensible repair cost estimation** (while staying conservative):

### Repair Estimator Inputs

```python
# Conservative rule-based band
repair_estimate_low = estimate_repair_cost(
    year_built=property_year,
    area_sqft=building_area,
    zoning=property_zoning,
    condition_flag=assessment_condition,  # if available
    region=city
)
# Output: $5k–$30k range (example)
```

### How It Works

```python
# Year-based depreciation multiplier
year_age = current_year - year_built
if year_age > 50:
    age_factor = 1.5  # Older = more repair needs
elif year_age > 30:
    age_factor = 1.2
else:
    age_factor = 1.0

# Size-based multiplier
repair_per_sqft = 15  # $/sqft conservative baseline
size_cost = (building_area or 1000) * repair_per_sqft

# Region multiplier (local cost of labor)
region_multipliers = {
    "Calgary": 0.95,    # Slightly cheaper
    "Edmonton": 1.0,    # Baseline
    "Toronto": 1.3,     # More expensive
    # etc.
}

# Combined estimate
base_repair = size_cost * age_factor
regional_repair = base_repair * region_multipliers.get(region, 1.0)

return {
    "estimate_low": regional_repair * 0.8,   # Conservative floor
    "estimate_mid": regional_repair,
    "estimate_high": regional_repair * 1.2   # Conservative ceiling
}
```

### When to Use Phase 3.1

✅ **DO** (Phase 3.1) if:
- You want to estimate repair bands from public data
- You understand it's defensible, not precise
- You're using it as a training signal, not a deal-killer rule

❌ **DON'T** (stay in Phase 3) if:
- You're not ready to tighten logic yet
- You want to rely purely on assessment value + human review
- You need actual inspection data (not estimates)

---

## Phase 3.1 Structure (Provisional)

If implemented, would look like:

```
services/api/public_training/
├── schema.py                    # Add repair_estimate_* fields
├── estimators/
│   └── repair_cost.py           # Rule-based repair estimation
└── preprocessors/
    └── augment_with_repairs.py  # Add to training records
```

Then in `generate_synthetic_outcomes.py`:

```python
# After loading assessment value
repair_estimate = estimate_repair_cost(
    year_built=property_year,
    area_sqft=building_area,
    zoning=property_zoning,
    region=city
)

# Adjust offer band
# offer = assessment_value - repairs - profit_margin
net_offer = (assessed_value - repair_estimate["estimate_mid"]) * 0.75

# Use for scoring: if net_offer < 0, reject deal
if net_offer < 0:
    should_pursue = False
    reason = "Negative spread after repair estimate"
```

---

## Data Expansion Roadmap (Future)

### Phase 3 (Current)
- ✅ Assessment value (AB)
- ✅ Synthetic labels (conservative)
- ✅ Replay metrics

### Phase 3.1 (Optional, still SANDBOX)
- Optional: Rule-based repair estimation
- Optional: Region cost multipliers
- Optional: Age-based depreciation

### Phase 4 (Future, if needed)
- Real MLS data (requires licensing)
- Actual inspection reports (requires partnerships)
- Historical sold price data (regional, macro only)

---

## Recommendation: Stay in Phase 3 for Now

**Why**: 
1. Assessment value + human review is already strong
2. Repair estimation is nice-to-have, not must-have
3. Better to validate basic wholesaling logic first
4. Phase 3.1 can be added later without breaking anything

**Action**:
1. Wire your wholesaling entrypoint (now)
2. Run replay with real scoring logic (next)
3. Check metrics against Go/No-Go gates (then)
4. If metrics are green, consider Phase 3.1 (later, optional)

---

## What's NOT Changing

- ✅ Hard APP_ENV gate (SANDBOX only)
- ✅ Training-only tables (never production)
- ✅ Conservative defaults
- ✅ Human-review flagging (≥80%)
- ✅ Golden tests (regression protection)

---

## Next Step

You're currently ready for **Phase 3 full execution**:

1. Run pipeline on Windows (commands in SANDBOX_TRAINING_QUICK_START.md)
2. Wire wholesaling adapter (provide entrypoint details)
3. Check metrics against Go/No-Go gates
4. Decide: Proceed to LIVE validation, or Phase 3.1?

Paste your wholesaling entrypoint whenever ready.
