# Heimdall Outcome Learning Loop Design

**Status:** Design Document (Vision for Adaptive Learning)  
**Created:** 2026-04-13  
**Purpose:** Document the feedback cycle that improves system intelligence over time.

---

## The Learning Loop (5-Step Cycle)

```
1. KNOWLEDGE ENTERS
   ↓
2. DEAL EXECUTED  
   ↓
3. OUTCOME RECORDED
   ↓
4. LESSON EXTRACTED
   ↓
5. RECOMMENDATIONS IMPROVE
   ↓
   (Back to step 1)
```

Each real deal becomes a data point that makes future recommendations smarter.

---

## Complete Example 1: Rehab Cost Mismatch

### Step 1: Knowledge Enters (Day 1)

**Source:** Memphis Market Report Q1 2026  
**Item:**
```
Title: "Average Rehab Cost Q1 2026"
Content: "Bathroom: $25-31k, Kitchen: $35-45k, Flooring: $8-15k..."
Confidence: 0.85
Status: "trusted"
```

**Insight:**
```
Text: "For wholesale deals in Memphis single-family, assume $28-32k bathroom"
Structured: {low: 28000, high: 32000, median: 30000}
Confidence: 0.90
```

### Step 2: Deal Executed (Days 2-28)

**Case CASE_001:**
```
Market: "memphis"
Strategy: "wholesale"
Asset Type: "single_family"
Condition: "fair"

Operator Intake: "3BR/1BA on Poplar Ave, needs bathroom, flooring work"

System Analysis:
- Estimated rehab cost: $30,000 (using Heimdall insight median)
- Estimated days to close: 14-21
- Decision: PROCEED
```

**Execution Flow:**
- POST /execution/intake → Creates case
- POST /execution/intake/{id}/process → Analysis engine runs
- GET /execution/cases/{id}/tasks → Tasks generated
- GET /execution/cases/{id}/next-action → Action queue
- POST /execution/cases/{id}/advance → Stage progression
- Deal closes

### Step 3: Outcome Recorded (Day 29)

**Operator records outcome:**
```
POST /heimdall/intelligence/outcomes
{
  "case_id": "CASE_001",
  "deal_id": "DEAL_2026_04_001",
  "market": "memphis",
  "strategy": "wholesale",
  "asset_type": "single_family",
  "predicted_result_json": {
    "estimated_arv": 185000,
    "estimated_rehab": 30000,
    "estimated_rehab_sources": ["bathroom:30000"],
    "estimated_close_days": 18,
    "estimated_total_profit": 15000
  },
  "actual_result_json": {
    "actual_arv": 188000,
    "actual_purchased_price": 162000,
    "actual_rehab_spent": 37500,
    "actual_rehab_breakdown": {
      "bathroom": 38000,
      "flooring": 8000,
      "electrical": 5000,
      "other": -13500
    },
    "actual_close_days": 32,
    "actual_total_profit": 8500,
    "notes": "Bathroom contractor overcharged; found hidden electrical issues"
  }
}
```

### Step 4: System Calculates Delta

```json
{
  "delta_json": {
    "arv_delta": 3000,
    "arv_delta_pct": 0.016,          // 1.6% low

    "rehab_cost_delta": 7500,         // MAJOR MISS
    "rehab_cost_delta_pct": 0.25,     // 25% underestimated!
    "bathroom_cost_delta": 8000,       // Bathroom was 26.7% high
    
    "close_days_delta": 14,            // 78% slower
    "close_days_delta_pct": 0.77,

    "profit_delta": -6500,             // 43% lower than predicted
    "profit_delta_pct": -0.43
  }
}
```

### Step 5: Lesson Extracted

**Operator records lesson:**
```
POST /heimdall/intelligence/outcomes/{outcome_id}/lesson
{
  "lesson_text": "Memphis single-family bathroom costs significantly underestimated. Last 2 deals also came in 22-28% over estimate for bathroom work. Recommend increasing baseline from $30k to $37.5k for Q2.",
  "applies_to": {
    "market": "memphis",
    "strategy": "wholesale",
    "asset_type": "single_family"
  },
  "confidence_score": 0.88,
  "data_supporting": [
    "DEAL_2026_04_001: Bathroom +$8k vs estimate",
    "DEAL_2026_03_012: Bathroom +$5.5k vs estimate",
    "DEAL_2026_02_018: Bathroom +$7.2k vs estimate"
  ]
}
```

### Step 6: Recommendations IMPROVE

**Next time (Day 50):**
```
POST /heimdall/intelligence/recommend
{
  "market": "memphis",
  "strategy": "wholesale",
  "asset_type": "single_family",
  "question": "What should we assume for bathroom rehab?"
}

RESPONSE (OLD - v1):
{
  "recommendation": "Assume $28-32k bathroom rehab",
  "confidence": 0.90,
  "supporting_evidence": [
    "Memphis Market Report - trust=high",
    "Baseline knowledge"
  ]
}

RESPONSE (NEW - v2, after learning):
{
  "recommendation": "Assume $35-40k bathroom rehab (Q2 updated)",
  "confidence": 0.94,
  "supporting_evidence": [
    "Memphis Market Report (historical)",
    "Recent 3-deal pattern: all bathroom work +22-27% vs estimate",
    "Hidden issues pattern: 2 of 3 recent deals found electrical/plumbing"
  ],
  "caveats": [
    "Recent trend shows costs rising; monitor Q3",
    "Previous estimate was $30k; contractor inflation evident"
  ]
}
```

### Step 7: Next Deal Uses Improved Data

**Case CASE_002 (Day 52):**
```
New intake: Similar property, similar condition

System now predicts:
- Bathroom rehab: $37.5k (was $30k)
- Expected margin: 8% (vs 10% before)
- Decision: Still proceed, but more realistic

Post-execution:
- Actual bathroom: $36.8k
- Much more accurate!
```

---

## Example 2: Seller Negotiation Pattern

### The Feedback Loop

**Timeline:**

**Day 1 - Knowledge:** "Sellers typically reduce 3-5% on second offer"  
**Days 2-20 - Deals:** 10 wholesale deals closed  
**Day 21 - Recording:**
```
Outcomes recorded:
- Deal 001: Seller reduced 2.1% on second offer
- Deal 002: Seller reduced 4.8% on second offer  
- Deal 003: Seller reduced 3.2% on second offer
- Deal 004: Seller reduced 2.9% on second offer
- Deal 005: Seller HELD FIRM (0% reduction)  ← Outlier
- Deal 006: Seller reduced 3.6% on second offer
- Deal 007: Seller reduced 2.4% on second offer  
- Deal 008: Seller reduced 5.1% on second offer
- Deal 009: Seller reduced 3.7% on second offer  
- Deal 010: Seller reduced 3.0% on second offer
```

**Day 22 - Lesson Generated:**
```
Pattern Analysis:
- 9 out of 10 sellers negotiated
- Range: 2.1% - 5.1%
- Average: 3.6%  ← Updated recommendation
- Outlier: Deal 005 was distressed property (different dynamics)
- Confidence: 0.92 (9-point sample)

Lesson: "Seller reduction baseline should be 3.5-3.7% in current market, 
not 3-5% range. Update confidence to HIGH. Note: Distressed properties 
may not negotiate."
```

**Day 23 - Recommendations Update:**
```
New recommendation: "Assume 3.6% seller reduction on second offer"
Confidence: 0.92 (up from 0.75)
Evidence: "Last 9 deals in market, 90% hit this range"

Corollary: "Use 3.6% as baseline for profit calculations"
```

---

## Example 3: Buyer Assignment Pattern (Hold Strategy)

### The Learning Process

**Phase 1: Baseline Knowledge Enters**
```
Source: REIA discussion forum + operator notes
Item: "Multifamily hold deals attract 60-80% of asking price from 
       institutional buyers within 30-day window"
Confidence: 0.65 (forum-based, less reliable)
Status: "reviewed"
```

**Phase 2: Initial Outcome Recording**
```
Deal 1: Listed at 8% cap rate, sold to investor at 7.2% (yes, 0.8% surprise)
Deal 2: Listed at 7.5% cap rate, sold to buyer at 7.8% (cap rate actually UP)
Deal 3: Listed at 8.2% cap rate, listed but not sold in window
Deal 4: Listed at 7.8% cap rate, sold at 7.9% (slight loss of premium)

Delta: Market showing strong buyer interest; prices holding or increasing
```

**Phase 3: Lesson Extracted**
```
Lesson: "Multifamily buyers are offering ABOVE asking in this market. 
Not 60-80% as forum said. More like 95-102% of offering cap rate. 
This is a strong market signal. Update confidence: 0.85. Update timeline: 
buyers responding within 7-14 days, not 30."
```

**Phase 4: Recommendations Change**
```
OLD: "Expect offers at 60-80% of asking, 30-day close"
NEW: "Expect multiple offers, 95-102% of cap rate, 7-14 day close"
Impact: Strategy switches from "flip" to "hold" for multifamily more often
Confidence: 0.85 (now backed by 4 local deals)
```

---

## Example 4: Lead Source Quality Tracking

### Loop in Action

**Setup:** Three lead sources being tracked

**Initial Knowledge:**
```
Source A (Zillow API): Unknown quality (new source)
Source B (Facebook Forum): Known quality (medium trust)  
Source C (Partner Network): High-quality referral

No baseline for quality comparison
```

**Month 1 Outcome Recording:**
```
From Source A: 12 leads → 3 deals → 25% close rate
From Source B: 18 leads → 4 deals → 22% close rate
From Source C: 5 leads → 4 deals → 80% close rate

Quality lesson: "Partner network is 3x more efficient; 
Zillow and Facebook roughly equivalent"
```

**Recommendations Update:**
```
Ranking by ROI:
1. Partner network (80% close, needs more volume)
2. Zillow API (25% close, good volume potential)  
3. Facebook forum (22% close, declining engagement)

Action: Prioritize partner network leads, scale Zillow capacity
```

**Decision Impact:**
```
New strategy: Focus acquisition efforts on:
1. Build partner relationships (highest quality)
2. Expand Zillow sourcing (volume + acceptable quality)  
3. De-emphasize Facebook (lower quality despite ok volume)

Expected outcome: 35%+ overall close rate (vs 23% current)
```

---

## Multi-Deal Pattern Recognition

### How Heimdall Learns from Patterns

**Scenario: 15 Wholesale Deals Over 4 Weeks**

**Pattern 1: Property Condition Assessment**
```
Deals analyzed: 15
Fair condition properties (n=5):
- Avg rehab cost mismatch: +18%
- Avg days to close: +23%  
- Avg profit delta: -$4,200

Poor condition properties (n=10):
- Avg rehab cost mismatch: +31%
- Avg days to close: +35%
- Avg profit delta: -$8,700

Lesson: "Condition assessment accuracy is our biggest cost driver.
Need more detailed inspection protocols. Poor condition deals need 30%+ 
buffer, not 15%."
```

**Pattern 2: Market Temperature**
```
Deals in hot markets (Memphis, Nashville): 8 deals
- Seller reduction: 2.1% average (vs 3.6% normal)
- Close time: +15% slower (higher competition)
- Margin erosion: -2.3% vs normal

Deals in cool markets (smaller towns): 7 deals
- Seller reduction: 4.8% average  
- Close time: -5% faster
- Margin: +1.1% vs normal

Action: Allocate more resources to cool markets; 
time wholesale pipeline for hot markets (they move anyway)
```

**Pattern 3: Outcome Accuracy Predictor**
```
When broker confidence = "high": 
- Accuracy of ARV estimate: 98%
- Outcome recorded within 5%: 92% of deals

When broker confidence = "medium":
- Accuracy of ARV estimate: 87%
- Outcome recorded within 5%: 67% of deals

When broker confidence = "low":
- Accuracy of ARV estimate: 71%
- Outcome recorded within 5%: 41% of deals

Insight: "Broker confidence is highly predictive of outcome accuracy.
Use as signal: if confidence low, add 8-12% buffer to estimates."
```

---

## Scaling: New Markets

### How Learning Transfers Across Markets

**Year 1: Memphis (100 outcomes recorded)**
```
Rehab cost patterns by property type
Lead source quality rankings
Negotiation patterns
Buyer behavior insights
Seasonal trends
```

**Year 1 → Year 2: Expanding to Nashville**
```
Transfer knowledge that's generalizable:
- Rehab cost categories (bathroom +20-25%, kitchen +40%, etc.)  
  These patterns likely similar
- Negotiation dynamics (sellers on second offer typically 3-5%)
  Market-independent pattern
- Buyer behavior (multifamily buyers look for 7-8% cap rate)
  Investor behavior market-independent

Start fresh on Nashville-specific:
- Local market trends
- Lead source quality (new referral network)
- Seasonal patterns (Tennessee-specific weather)
```

**Result:**
```
Nashville ramp-up accelerated by 30-40% due to Memphis patterns
Can make confident portfolio projections within 3-4 deals vs 10+ needed

Heimdall transfers institutional knowledge efficiently
```

---

## Confidence Evolution Over Time

### Single Knowledge Item Confidence Journey

**"Wholesale profit margin in Memphis"**

```
Week 1 (New knowledge)
├─ Source: Public forum
├─ Initial confidence: 0.55
├─ Status: "reviewed"
└─ Usage: Advisory only, not in decisions

Week 4 (First outcome data)  
├─ 2 deals recorded
├─ Prediction: 15% margin, Actual: 12% and 14%
├─ Lesson: "Close but 3-4% high"
├─ Updated confidence: 0.62
└─ Status: "reviewed" → "trusted"

Week 8 (More data)
├─ 5 more deals recorded
├─ Predictions: 14%, 13%, 12%, 15%, 11%
├─ Actual: 7%, 11%, 10%, 13%, 9%
├─ Pattern: Consistently 2-3% high
├─ Lesson: "Adjust down 3%; confidence_high"
├─ Updated confidence: 0.82
└─ Status: still "trusted"

Week 12 (Baseline established)
├─ 10 deals, strong pattern
├─ Predictions well-calibrated
├─ Confidence: 0.88
├─ Status: "trusted" (high confidence)
└─ Now used actively in strategy selection
```

---

## When Learning Saves Money

### Example: Avoided Loss Through Pattern Recognition

**Scenario: New Contractor (Lesson Would Have Helped)**

```
History (if it existed):
3 previous deals with "new contractor" label:
- Timelines: +25%, +31%, +18% vs estimate
- Costs: +12%, +8%, +15% vs estimate
- Quality issues: 2 of 3 required rework

Lesson stored: "New contractors add 15-20% buffer needed"

New deal without this lesson:
- Budget: $30k based on established contractor rate
- Reality: Contractor overruns to $38k
- Loss: $8k profit erosion

New deal WITH Heimdall lesson:
- Budget: $36k (15% buffer applied)
- Reality: Contractor at $38k (within buffer)
- Loss avoided: Profitability maintained
```

---

## Positive Compounding

### Heimdall's Value Over 12 Months

**Month 1:** 15 deals  
- Baseline established
- Confidence: 0.65-0.75 on most topics
- 10-15% margin deterioration from estimates

**Month 3:** 45 deals cumulative  
- Clear patterns emerging
- Confidence: 0.78-0.85
- 5-8% margin deterioration (improved)

**Month 6:** 90 deals cumulative  
- Multi-pattern analysis active
- Confidence: 0.85-0.92
- 2-4% margin deterioration (very good)
- Predictions now valuable → feed into decisions

**Month 9:** 135 deals cumulative  
- Seasonal patterns identified
- Multi-market patterns transferable
- Confidence: 0.90-0.95
- Prediction accuracy within 2-3%
- New markets can leverage 30-40% knowledge transfer

**Month 12:** 180 deals cumulative  
- Comprehensive institutional knowledge
- Confidence: 0.92-0.96 across categories
- Prediction accuracy <2%
- System adapts to team, market conditions, seasonal shifts
- New acquisitions can leverage full data library
```

---

## Summary: The Loop in 5 Stages

| Stage | Activity | Data | Confidence |
|-------|----------|------|-----------|
| 1 | Knowledge ingestion | Source info + content | Initial (0.5-0.8) |
| 2 | Deal execution | Case routing + decisions | Baseline established |
| 3 | Outcome recording | Predicted vs actual | Gap analysis computed |
| 4 | Lesson extraction | Patterns + deltas | Confidence adjusted |
| 5 | Recommendation improvement | Updated guidance | Confidence 0.85-0.95+ |

**Flywheel effect:** Better recommendations → better deal selection → better outcomes → even better recommendations

---

## Next Phases for Learning

**Phase 1 (Now):** Manual outcome recording by operators  
**Phase 2 (Month 1):** Automated outcome capture from execution layer  
**Phase 3 (Month 3):** Multi-market pattern analysis  
**Phase 4 (Month 6):** Predictive model integration  
**Phase 5 (Month 9):** Autonomous learning recommendations (still advisory)  
**Phase 6 (Year 1+):** Full adaptive learning system  

---

**Key Message:** Every deal is data. Every outcome is a lesson. Every lesson makes the next decision better. This is not just knowledge storage—it's an adaptive learning system that gets smarter with every execution.
