# Heimdall Intelligence Layer V1 — Overview

**Status:** Design & Foundation Build (Non-Breaking, Human-Guided)  
**Created:** 2026-04-13  
**Purpose:** Build the first working learning-memory layer to store, normalize, and score knowledge while recording outcome feedback from real operations.

---

## Executive Summary

**Heimdall Intelligence V1** is a human-guided knowledge management and outcome learning system that sits alongside the live execution layer (NOT replacing it). It captures:

1. **Public Knowledge** — market trends, negotiation patterns, rehab costs, legal constraints
2. **Internal Outcomes** — actual deal results, strategy performance, lesson observations  
3. **Structured Insights** — normalized, weighted, confidence-scored knowledge
4. **Decision Memory** — recommendations paired with actual decisions and outcomes

This layer prepares the system for **future adaptive learning** without requiring autonomous internet scraping or external API integrations today.

---

## What It Does (Phase 1)

✅ **Store Public Knowledge**
- Accept manually curated or guided ingestion of market knowledge
- Persist knowledge items with source tracking and confidence scores
- Categorize by market, strategy, asset type, knowledge type

✅ **Normalize & Structure**
- Accept raw knowledge, store structured insights and summaries
- Tag with applicable strategy, market, and asset type
- Support both free-text and structured value entry

✅ **Weight & Score Confidence**
- Assign trust levels to sources (government, operator, forum, report)
- Assign confidence to individual insights (high, medium, low)
- Enable relevance scoring based on current market context

✅ **Connect to Decision Context**
- Link knowledge to market, strategy, and deal type
- Store predicted vs. actual outcomes
- Calculate confidence adjustments based on mismatches

✅ **Record Outcome Feedback**
- After execution, capture what was predicted vs. what actually happened
- Extract lessons learned
- Build historical memory of strategy + market performance

✅ **Prepare for Adaptive Learning**
- Structure data to support future learning algorithms
- Keep audit trail of recommendations and outcomes
- Enable future comparison of predicted vs. actual across thousands of deals

---

## What It Does NOT Do (Phase 1)

❌ **Autonomous Internet Scraping**
- No background jobs crawling the web
- No API subscriptions to market data providers
- All data entry is manual or operator-guided

❌ **Live Decision Automation**
- Does NOT override current execution logic
- Does NOT auto-generate case decisions
- Does NOT modify risk scoring without explicit opt-in

❌ **Real-Time Market Tracking**
- Does NOT stream market updates
- Does NOT perform live competitive analysis
- Does NOT auto-adjust strategy based on market shifts

❌ **Complex ML/AI Integration**
- Does NOT call external LLM APIs
- Does NOT build proprietary models
- Does NOT make autonomous predictions yet

❌ **Operational Automation**
- Does NOT auto-assign tasks
- Does NOT auto-send communications
- Does NOT bypass human review

---

## Core Concepts

### Knowledge Sources
Where knowledge comes from. Examples:
- Government agencies (tax assessor, court records)
- Public web sources (market reports, forums)
- Operator notes (lessons from completed deals)
- Imported documents (market analysis, negotiation templates)

### Knowledge Items
Individual pieces of knowledge. Examples:
- **Rehab Cost:** "Average bathroom rehab in Nashville = $25k (2Q2026)"
- **Negotiation Pattern:** "Seller typically drops 5-8% after second offer"
- **Buyer Behavior:** "Hedge funds buying 100+ units prefer > 4% cap rate"
- **Market Trend:** "Remote work boost reducing office demand in Oklahoma City"

### Knowledge Insights
Structured, actionable interpretations of knowledge items. Examples:
- "For wholesale deals in Memphis, assume $28-32k rehab budget"
- "Partnership strategy requires seller willingness to restructure payment"
- "Commercial multifamily in Austin demand spike = hold strategy more attractive"

### Outcome Feedback
Real results from closed deals, paired with what was predicted. Enables learning:
- "Predicted rehab: $22k, Actual: $31k (Delta: +$9k, +41%)"
- "Strategy: Hold, Market: Tampa, ARV estimate was 8% high — adjust future estimates down 5%"
- "Lesson: Foreclosure properties have hidden liens 23% of the time"

### Decision Memory
Historic record of what was recommended, what was decided, and what the outcome was:
- Recommendation: "Wholesale deal — target $185k"
- Decision taken: "Offered $192k (7% above target)"
- Outcome score: "Closed at $188k, $3k loss vs. target"
- Lesson: "In hot markets, seller expectations anchored too high"

---

## Data Architecture (High Level)

```
┌─────────────────────────────────────────────────────────┐
│        HEIMDALL INTELLIGENCE LAYER V1                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Knowledge    │  │ Knowledge    │  │ Knowledge    │ │
│  │ Sources      │  │ Items        │  │ Insights     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Outcome      │  │ Decision     │  │ Market       │ │
│  │ Feedback     │  │ Memory       │  │ Memory       │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ (Non-Breaking)
                          ↓
┌─────────────────────────────────────────────────────────┐
│        EXECUTION LAYER (UNCHANGED)                      │
│  Cases → Decisions → Outcomes (feeds back to Heimdall) │
└─────────────────────────────────────────────────────────┘
```

---

## Integration Strategy (Future, Not Live)

**Phase 1 (Now):** Build isolated Heimdall layer with own routes, service, schemas
**Phase 2 (Post-WeWeb):** Add optional bridge functions to enrich execution context
**Phase 3 (Month 2+):** Activate learning feedback loop from execution cases
**Phase 4 (Future):** Enable adaptive strategy selection based on historical performance

**Critical:** No changes to execution layer except through opt-in bridge helpers.

---

## Success Criteria (V1)

✅ Knowledge sources can be registered and listed  
✅ Knowledge items can be ingested with source tracking  
✅ Knowledge insights can be extracted and stored  
✅ Searches return relevant knowledge by market/strategy  
✅ Outcome feedback can be recorded after execution  
✅ Lessons can be generated from prediction/actual deltas  
✅ Market memory snapshot can be generated  
✅ Zero impact on live execution endpoints  
✅ All data persisted (structure ready for migrations)  
✅ Audit trail complete  

---

## Tech Stack

**Framework:** FastAPI (same as execution layer)  
**Schemas:** Pydantic v2  
**Service Layer:** Python classes with stubbed logic  
**Data Storage:** PostgreSQL (via SQLAlchemy models — migrations deferred)  
**API:** RESTful, JSON request/response  
**Auth:** Inherit from existing execution auth (if present)  

---

## Code Structure (Phase 1)

```
app/
├── core/
│   ├── knowledge_types.py         (constants)
│   ├── source_types.py             (constants)
│   ├── strategy_types.py           (constants)
│   ├── knowledge_status.py         (constants)
│   ├── market_tags.py              (OPTIONAL)
│   ├── asset_types.py              (OPTIONAL)
│   └── trust_levels.py             (OPTIONAL)
├── schemas/
│   └── heimdall_intelligence.py    (Pydantic request/response)
├── services/
│   ├── heimdall_intelligence_service.py  (core logic)
│   └── heimdall_intelligence_bridge.py   (optional execution bridge)
├── routers/
│   └── heimdall_intelligence.py    (endpoints)
└── models/
    └── (NO NEW DB MODELS YET — planned in optional section)
```

---

## Next Steps

1. ✅ Phase 1: Design documents (this overview + data flow + route plan)
2. ⏳ Phase 2: Core data model documentation + code stubs
3. ⏳ Phase 3: Constants/enums (knowledge_types, source_types, etc.)
4. ⏳ Phase 4: Pydantic schemas (request/response structures)
5. ⏳ Phase 5: Service layer (stubbed, safe logic)
6. ⏳ Phase 6: Routes (isolated endpoints)
7. ⏳ Phase 7: Execution integration docs (future wiring)
8. ⏳ Phase 8: Outcome learning loop design
9. ⏳ Phase 9: WeWeb prep scope
10. ⏳ Phase 10: Optional safe files
11. ⏳ Phase 11: Optional DB migration plan (deferred)
12. ⏳ Phase 12: Final summary

---

## Watch-Out List

⚠️ **DO NOT** apply database migrations in Phase 1  
⚠️ **DO NOT** wire directly into execution cases without bridge layer  
⚠️ **DO NOT** create autonomous background jobs  
⚠️ **DO NOT** call external APIs or trigger web requests  
⚠️ **DO NOT** modify existing execution routes  
⚠️ **DO NOT** create browser automation or scraping logic  

All work is additive, safe, and reversible.

---

**Status:** Ready to proceed to Phase 2 (data model documentation + code stubs)
