# Heimdall Intelligence Layer V1 — Data Flow

**Status:** Design Document  
**Created:** 2026-04-13  
**Purpose:** Map how knowledge enters, flows through, and integrates with operational outcomes.

---

## Knowledge Ingestion Flow

### Entry Point 1: Manual Knowledge Registration

**Actor:** Operator, Manager, or Data Team  
**Trigger:** Identified knowledge source that should be captured  
**Flow:**

```
1. Register Source
   POST /heimdall/intelligence/sources
   {
     "source_name": "Memphis Market Report Q1 2026",
     "source_type": "market_report",
     "source_url": "https://...",
     "jurisdiction": "TN",
     "market": "memphis",
     "category": "market_trends",
     "trust_level": "high"
   }
   → Returns source_id

2. Add Knowledge Item(s)
   POST /heimdall/intelligence/items
   {
     "source_id": 42,
     "title": "Average Rehab Cost Q1 2026",
     "content_raw": "Full text from report",
     "content_summary": "Bathroom rehabs now $26-32k, kitchen $35-45k",
     "knowledge_type": "rehab_cost",
     "market": "memphis",
     "strategy": ["wholesale", "flip"],
     "asset_type": "single_family",
     "tags_json": ["cost_driven", "seasonal", "labor_intensive"],
     "confidence_score": 0.85
   }
   → Returns knowledge_item_id

3. Add Structured Insights
   POST /heimdall/intelligence/items/{item_id}/insights
   {
     "insight_text": "For wholesale deals in Memphis, assume $28-32k bathroom rehab",
     "structured_value_json": {
       "low": 28000,
       "high": 32000,
       "median": 30000,
       "category": "bathroom"
     },
     "applicable_market": "memphis",
     "applicable_strategy": "wholesale",
     "confidence_score": 0.90
   }
   → Stored in decision memory
```

**Result:** Knowledge persisted with source tracking, categorization, and confidence scoring.

---

### Entry Point 2: Guided Historical Data Import

**Actor:** Data Team or Specialist  
**Trigger:** Need to capture institutional knowledge or historical patterns  
**Flow:**

```
1. Bulk source creation (multiple market reports)

2. Knowledge items created from document review
   - Operator notes about past deals
   - Market analysis summaries
   - Negotiation outcome patterns
   - Legal constraint summaries

3. Insights extracted manually or via structured prompts
   - What does this mean for our strategies?
   - When is this applicable?
   - How confident are we?
```

**Result:** Historical knowledge base built, confidence levels assigned by human judgment.

---

## Knowledge Discovery & Application Flow

### Search & Retrieve

**Actor:** Operator looking for context  
**Trigger:** Starting to work a new case  
**Flow:**

```
1. Query Knowledge
   POST /heimdall/intelligence/search
   {
     "market": "nashville",
     "strategy": "wholesale",
     "asset_type": "single_family",
     "keywords": ["rehab", "cost"],
     "knowledge_types": ["rehab_cost", "market_trend"]
   }

2. Response Returns
   - Matching knowledge items with confidence scores
   - Applicable insights
   - Source information (trust level, date)
   - Tags and applicability

   [
     {
       "knowledge_item_id": 25,
       "title": "Average Rehab Cost Q1 2026",
       "content_summary": "...",
       "confidence": 0.90,
       "source": "Memphis Market Report",
       "applicable_strategy": "wholesale",
       "created_at": "2026-04-10"
     },
     ...
   ]
```

**Result:** Operator has knowledge context for decision-making (currently advisory, not automated).

---

### Insight Recommendation

**Actor:** System or Operator requesting recommendation  
**Trigger:** Need guidance on strategy, market, or approach  
**Flow:**

```
1. Request Recommendation
   POST /heimdall/intelligence/recommend
   {
     "market": "nashville",
     "strategy": "wholesale",
     "asset_type": "single_family",
     "condition": "fair",
     "question": "What should we assume for rehab costs?"
   }

2. Service Retrieves
   - High-confidence insights for this market/strategy/type
   - Recent outcome feedback that refines estimates
   - Historical decision memory showing success/failure

3. Response
   {
     "recommendation": "Assume $26-32k rehab budget",
     "confidence": 0.88,
     "supporting_evidence": [
       "Memphis Market Report (trust=high)",
       "3 last 5 recent wholesale deals hit mid-range",
       "No recent data suggesting seasonal shift"
     ],
     "caveats": [
       "Commercial properties may vary by 10-15%",
       "Minor cosmetic rehabs historically underestimated"
     ]
   }
```

**Result:** Operator has data-backed recommendation (current phase: advisory only).

---

## Operational Outcome Recording Flow

### When an Execution Case Completes

**Actor:** Operator or System (future)  
**Trigger:** Case closes (deal completed or dropped)  
**Flow:**

```
1. Capture Execution Outcome
   GET /execution/cases/{case_id}
   → Retrieves full case history, decisions, and final state

2. Record in Heimdall (Manual or Automated Later)
   POST /heimdall/intelligence/outcomes
   {
     "case_id": 123,
     "deal_id": "DEAL_2026_04_001",
     "market": "nashville",
     "strategy": "wholesale",
     "predicted_result_json": {
       "estimated_arv": 185000,
       "estimated_rehab": 30000,
       "estimated_profit": 15000,
       "confidence": 0.85
     },
     "actual_result_json": {
       "actual_arv": 188000,
       "actual_rehab": 35000,
       "actual_profit": 8000,
       "deal_duration_days": 28
     }
   }

3. System Calculates Delta
   {
     "arv_delta": +3000,      // estimate was 1.6% LOW
     "rehab_delta": +5000,    // estimate was 16.7% LOW
     "profit_delta": -7000,   // estimate was 46.7% HIGH
     "confidence_adjustment": -0.08  // reduce future confidence in this type
   }

4. Generate Lesson
   POST /heimdall/intelligence/outcomes/{id}/lesson
   {
     "lesson_text": "Single-family rehab estimates in Nashville are underestimated by 15-20%. Adjust baseline +15% in future.",
     "applies_to": {
       "market": "nashville",
       "strategy": "wholesale",
       "asset_type": "single_family"
     },
     "confidence_score": 0.82
   }
```

**Result:** Outcome recorded, delta calculated, lesson extracted, confidence scores revised.

---

## Decision Memory Building Flow

### After Outcome Recorded

**Actor:** System or Operator (manual review)  
**Trigger:** Outcome lesson generated  
**Flow:**

```
1. Extract Learning Point
   Recommended: $30k rehab budget
   Actual: $35k rehab budget
   Pattern: Last 5 single-family wholesales averaged +16% vs. estimate

2. Update Decision Memory
   {
     "subject_type": "rehab_budget",
     "subject_id": "nashville_wholesale_sf",
     "market": "nashville",
     "strategy": "wholesale",
     "recommendation_text": "Use $34.5k baseline (was $30k)",
     "decision_taken": "Still using old $30k baseline",
     "outcome_score": -0.16,  // 16% worse than expected
     "lesson_text": "Need to increase baseline by 15% based on 5-deal pattern"
   }

3. Next Time Query Returns Updated Data
   - Old recommendation: $30k (now marked as deprecated)
   - New recommendation: $34.5k (based on recent feedback)
   - Confidence: 0.80 (adjusted from 0.85 due to systematic miss)
```

**Result:** Decision memory continuously updated with real outcome data.

---

## Market Memory Snapshot Flow

### Request Current Market State

**Actor:** Manager or Strategist  
**Trigger:** Need market context for planning  
**Flow:**

```
1. Request Market Snapshot
   GET /heimdall/intelligence/market-memory
   ?market=nashville
   &strategy=wholesale
   &asset_type=single_family

2. Service Aggregates
   - High-confidence knowledge for this market
   - Recent outcome data (last 30 days)
   - Decision memory showing performance trends
   - Source diversity (ensure not single-sourced)

3. Response
   {
     "market": "nashville",
     "strategy": "wholesale",
     "asset_type": "single_family",
     "primary_insights": [
       {
         "title": "Rehab Cost Baseline",
         "value": "$34,500",
         "confidence": 0.88,
         "last_updated": "2026-04-13",
         "data_points": 5
       },
       {
         "title": "Target ARV Accuracy",
         "value": "98%",
         "confidence": 0.75,
         "trend": "improving"
       }
     ],
     "recent_outcomes": [
       { "deal_date": "2026-04-12", "profit_delta": +2000, "lesson": "... " },
       { "deal_date": "2026-04-11", "profit_delta": -1500, "lesson": "... " }
     ],
     "overall_confidence": 0.82,
     "knowledge_sources": 8,
     "deals_in_memory": 23
   }
```

**Result:** Leadership has data-backed market assessment.

---

## Non-Breaking Integration Pattern (Phase 1)

### Heimdall Stays Isolated

```
EXECUTION LAYER                    HEIMDALL LAYER
─────────────────────              ──────────────────

POST /execution/intake             (independent)
  ↓ Creates case
  ├─→ Case saved to DB
  ├─→ Decision made
  └─→ Outcome recorded (later)      → POST /heimdall/intelligence/outcomes
                                      (manual or automated bridge)

No changes to /execution routes
No changes to execution models
No dependencies in either direction (YET)
```

### Bridge Layer (Optional, Future)

When ready to connect:

```
app/services/heimdall_intelligence_bridge.py

• get_market_insights_for_strategy(market, strategy)
  → Returns high-confidence insights without modifying execution

• get_recent_lessons_for_market(market)
  → Returns trend data for human decision context

• get_knowledge_hints_for_case(case)
  → Returns applicable knowledge for case without auto-deciding

These helpers are ADVISORY ONLY.
They do not override execution logic.
They do not change case processing.
```

---

## Data Persistence (Deferred)

### Phase 1: In-Memory or Optional DB

All data structures are designed for PostgreSQL persistence via SQLAlchemy, but:
- **Phase 1 (Now):** Can run with in-memory storage or optional DB models
- **Phase 2 (Post-WeWeb):** When ready, apply safe migrations
- **No time pressure:** Build logic first, database second

### Why Defer:
✅ Reduces deployment risk  
✅ Allows logic validation first  
✅ Keeps focus on API design and service layer  
✅ Migrations can be generated cleanly once models are proven  

---

## Audit & Tracking

**Every Heimdall operation tracked:**
- Source registered → logged with timestamp and actor
- Knowledge item created → logged with source reference
- Outcome recorded → linked to execution case
- Lesson generated → logged with supporting evidence
- Recommendation delivered → logged with request context

**Result:** Full audit trail for confidence scoring and future learning validation.

---

## Success Criteria: Data Flow

✅ Knowledge enters without errors  
✅ Insights are searchable and retrievable  
✅ Outcomes pair with predictions  
✅ Lessons are extractable  
✅ Market memory snapshots are consistent  
✅ Zero data loss on operations  
✅ Full audit trail maintained  
✅ No interference with execution layer  

---

## Next Phase

→ Phase 2: Core Data Model Documentation + Code Stubs
