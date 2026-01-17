# Governance Orchestrator - Quick Start

## One-Minute Overview

The **Governance Orchestrator** is your single unified interface to evaluate any business decision against five independent governance gods:

- **KING**: Checks financial risk/ROI and mission alignment
- **QUEEN**: Checks energy levels and team sustainability  
- **ODIN**: Checks vertical focus and strategy alignment
- **LOKI**: Checks worst-case downside and ruin probability
- **TYR**: Checks legal/ethical boundaries (hard-stops)

### The Endpoint

```
POST /api/governance/evaluate_all
```

### The Request

```json
{
  "context_type": "deal",
  "data": {
    "purchase_price": "200000",
    "repairs": "20000",
    "roi": "0.25",
    "hours_per_week": "40",
    "stress_level": "5",
    "active_verticals": "2",
    "distraction_score": "3",
    "capital_at_risk": "80000",
    "worst_case_loss": "60000",
    "probability_of_ruin": "0.02",
    "tax_evasion": "False"
  },
  "gods": null  // null or omit = check all 5
}
```

### The Response

```json
{
  "overall_allowed": true,
  "worst_severity": "warn",
  "blocked_by": [],
  "checks": [
    {
      "god": "king",
      "allowed": true,
      "severity": "info",
      "reasons": [],
      "notes": "King approves..."
    },
    // ... one entry per god checked
  ],
  "summary": "Plan allowed with warnings..."
}
```

## Decision Logic

| Result | Meaning |
|--------|---------|
| `overall_allowed: true` | All gods approve (warnings OK) |
| `overall_allowed: false` | At least one god issued critical denial |
| `worst_severity: critical` | Someone disagreed strongly |
| `blocked_by: ["tyr"]` | Which gods said "no" |

## 3 Ways to Use It

### 1. Check All Five Gods (Default)

```python
result = client.post("/api/governance/evaluate_all", json={
    "context_type": "deal",
    "data": {...},
    "gods": None  # Check all 5
}).json()
```

### 2. Check Specific Gods

```python
result = client.post("/api/governance/evaluate_all", json={
    "context_type": "new_vertical",
    "data": {...},
    "gods": ["odin", "queen"]  # Only these two
}).json()
```

### 3. Integrate Into Your Code

```python
def approve_deal(deal):
    response = client.post("/api/governance/evaluate_all", json={
        "context_type": "deal",
        "data": deal.to_dict(),
        "gods": None
    })
    
    result = response.json()
    
    if result["overall_allowed"]:
        execute_deal(deal)
        return {"status": "approved"}
    else:
        return {
            "status": "rejected",
            "blocked_by": result["blocked_by"],
            "reason": result["summary"]
        }
```

## What Each God Checks

### KING
- ✅ Investment size under $500k?
- ✅ ROI above 12%?
- ✅ Repairs under 30% of purchase?
- ✅ Not predatory?
- ✅ Aligned with mission?

### QUEEN
- ✅ Hours/week under 40?
- ✅ Not using evenings/weekends?
- ✅ Parallel projects ≤ 3?
- ✅ Stress level ≤ 7?
- ✅ Sprint duration 2-4 weeks?

### ODIN
- ✅ Active verticals ≤ 5?
- ✅ High profit vs low complexity?
- ✅ Break-even in 12-18 months?
- ✅ Strategic alignment?
- ✅ Not a distraction?

### LOKI
- ✅ Worst-case loss < 1.5x capital at risk?
- ✅ Ruin probability < 5%?
- ✅ Portfolio correlation < 80%?
- ✅ Hidden complexity manageable?

### TYR (Hard-Stops Only)
- ❌ No unlicensed practice
- ❌ No tax evasion
- ❌ No fraud
- ❌ No illegal recording
- ❌ No exploitation
- ❌ No misleading marketing
- ❌ No incomplete disclosures

**KEY**: Tyr is the only god that ALWAYS denies violations. Other gods warn. Tyr blocks.

## Test Results

```
✓ All 5 gods operational
✓ Orchestrator fully functional
✓ 25/25 tests passing
✓ 0 deprecation warnings
✓ Ready for production
```

## Next Steps

1. **Integrate into deal pipeline**
   ```python
   # Before executing any deal, run governance check
   if not governance_check(deal).overall_allowed:
       return reject_deal(deal)
   ```

2. **Add to profit distribution**
   ```python
   # Before allocating profits, check budget constraints
   governance_check(profit_allocation)
   ```

3. **Gate Heimdall autonomous operations**
   ```python
   # Before Heimdall builds something, get gods' approval
   if heimdall.should_build(request):
       if governance_check(request).overall_allowed:
           heimdall.execute(request)
   ```

## All Gods Together = Governance Spine

The five gods form a **governance spine** that:
- Ensures financial soundness (King)
- Protects team health (Queen)
- Maintains focus (Odin)
- Guards downside (Loki)
- Enforces ethics/law (Tyr)

This prevents Heimdall from doing reckless things while allowing safe innovation.

---

**Ready to use?** POST to `/api/governance/evaluate_all` with your context data!
