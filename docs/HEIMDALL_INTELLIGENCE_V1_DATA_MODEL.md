# Heimdall Intelligence Layer V1 — Data Model

**Status:** Design Document + Code Stubs Reference  
**Created:** 2026-04-13  
**Purpose:** Define core data structures and their relationships; reference code generation without breaking DB.

---

## Model Overview

**5 Core Concepts:**

1. **KnowledgeSource** — Where knowledge comes from (trust level, categorization)
2. **KnowledgeItem** — Individual pieces of knowledge (raw + summary, confidence)
3. **KnowledgeInsight** — Structured, actionable interpretations (confidence-scored)
4. **OutcomeFeedback** — Actual vs. predicted results from real deals (delta analysis)
5. **DecisionMemory** — Historic record of recommendations, decisions, and outcomes

**Relationships:**

```
KnowledgeSource (1) ──→ (Many) KnowledgeItem
                              │
                              └─→ (Many) KnowledgeInsight

OutcomeFeedback ──→ (links to) ExecutionCase (external, in execution layer)
                │
                └─→ (generates) Lesson

DecisionMemory ──→ (updated by) OutcomeFeedback
```

---

## 1. KnowledgeSource

**Purpose:** Represent a source of knowledge (report, forum, operator, government)

### Fields

| Field | Type | Size | Nullable | Default | Purpose |
|-------|------|------|----------|---------|---------|
| id | UUID/Serial | — | NO | PK | Primary key |
| source_name | String | 255 | NO | — | Human-readable name (e.g., "Memphis Market Report Q1 2026") |
| source_type | Enum | — | NO | — | Type of source (government, public_web, forum, community, market_report, internal_outcome, operator_note, imported_doc) |
| source_url | String | 1024 | YES | NULL | URL if applicable |
| jurisdiction | String | 10 | YES | NULL | Geographic jurisdiction (e.g., "TN", "US", "GLOBAL") |
| market | String | 50 | YES | NULL | Market code if market-specific (e.g., "memphis", "nashville") |
| category | String | 100 | YES | NULL | Content category (e.g., "market_trends", "legal_constraints", "rehab_costs") |
| trust_level | Enum | — | NO | "medium" | Trust score for source (high, medium, low) |
| active | Boolean | — | NO | true | Whether this source is currently active |
| created_at | DateTime | — | NO | NOW() | When source was registered |
| updated_at | DateTime | — | NO | NOW() | Last update |
| created_by | String | 255 | YES | NULL | Who registered this source |

### Rationale

- **source_type:** Enables filtering by how reliable the source is
- **jurisdiction + market:** Allows geographic/market-specific queries
- **trust_level:** Pre-assessment of source reliability
- **active:** Allows deprecating sources without deleting history
- **created_by + created_at:** Audit trail for knowledge provenance

### Example Records

```
1. source_name: "Memphis REIA 2026 Buyer Survey"
   source_type: "community"
   source_url: "https://www.memphisreia.org"
   market: "memphis"
   trust_level: "high"

2. source_name: "County Tax Assessor Records"
   source_type: "government"
   jurisdiction: "TN"
   market: "nashville"
   trust_level: "high"

3. source_name: "Operator Note - John Doe"
   source_type: "operator_note"
   trust_level: "medium"
```

---

## 2. KnowledgeItem

**Purpose:** Store individual pieces of knowledge with categorization and confidence

### Fields

| Field | Type | Size | Nullable | Default | Purpose |
|-------|------|------|----------|---------|---------|
| id | UUID/Serial | — | NO | PK | Primary key |
| source_id | FK | — | NO | — | Foreign key to KnowledgeSource |
| title | String | 500 | NO | — | Title of knowledge item |
| content_raw | Text | — | YES | — | Full original text/document |
| content_summary | Text | — | YES | — | Short summary (operators can read quickly) |
| knowledge_type | Enum | — | NO | — | Type of knowledge (see enum below) |
| market | String | 50 | YES | NULL | Market applicability (e.g., "memphis") |
| strategy | JSON | — | YES | NULL | Array of applicable strategies (e.g., ["wholesale", "flip"]) |
| asset_type | String | 50 | YES | NULL | Asset type applicability (e.g., "single_family", "multifamily") |
| tags_json | JSON | — | YES | NULL | Free-form tags array (e.g., ["cost_driven", "seasonal"]) |
| confidence_score | Float | — | NO | 0.5 | Confidence this knowledge is accurate (0.0-1.0) |
| status | Enum | — | NO | "draft" | Status of item (draft, reviewed, trusted, deprecated, rejected) |
| created_at | DateTime | — | NO | NOW() | When ingested |
| updated_at | DateTime | — | NO | NOW() | Last update |
| created_by | String | 255 | YES | NULL | Who ingested this |

### Knowledge Type Enum

```python
KnowledgeType = Enum(
    "rehab_cost",              # Estimated costs for specific repairs
    "market_trend",            # Regional market patterns/cycles
    "negotiation_pattern",     # Buyer/seller negotiation behavior
    "legal_constraint",        # Legal/regulatory requirements
    "lead_source_pattern",     # Patterns from lead sources
    "buyer_behavior",          # How buyers in a market behave
    "seller_behavior",         # How sellers in a market behave
    "rent_estimate",           # Estimated rental rates
    "arv_estimate",            # After-repair value estimates
    "financing_pattern",       # Financing options/terms available
    "tax_rule",                # Tax implications
    "operational_rule",        # Operational constraints or best practices
)
```

### Rationale

- **content_raw + summary:** Preserve original + allow quick reading
- **market + strategy + asset_type:** Enable precise filtering/recommendations
- **tags_json:** Flexible categorization without schema changes
- **confidence_score + status:** Allow curation and confidence tracking
- **knowledge_type:** Critical for recommendations and filtering

### Example Records

```
1. title: "Average Rehab Cost Q1 2026"
   source_id: 1
   knowledge_type: "rehab_cost"
   market: "memphis"
   strategy: ["wholesale", "flip"]
   asset_type: "single_family"
   content_summary: "Bathroom rehabs $26-32k, kitchen $35-45k, flooring $8-15k"
   confidence_score: 0.88
   status: "trusted"

2. title: "Seller Negotiation Pattern - Counteroffer Strategy"
   source_id: 3
   knowledge_type: "negotiation_pattern"
   strategy: ["wholesale", "partnership"]
   content_summary: "Sellers typically reduce asking price 2-5% on first counteroffer"
   confidence_score: 0.72
   status: "reviewed"

3. title: "Memphis Market Shift - Tech Company Relocations"
   source_id: 2
   knowledge_type: "market_trend"
   market: "memphis"
   tags_json: ["employment", "demographic_shift", "upside_opportunity"]
   confidence_score: 0.80
   status: "trusted"
```

---

## 3. KnowledgeInsight

**Purpose:** Store structured, actionable interpretations with high confidence

### Fields

| Field | Type | Size | Nullable | Default | Purpose |
|-------|------|------|----------|---------|---------|
| id | UUID/Serial | — | NO | PK | Primary key |
| knowledge_item_id | FK | — | NO | — | Foreign key to KnowledgeItem |
| insight_text | String | 1000 | NO | — | Human-readable insight (e.g., "For wholesale in Memphis, assume $28-32k bathroom rehab") |
| structured_value_json | JSON | — | YES | NULL | Structured data (e.g., {low: 28000, high: 32000, median: 30000}) |
| applicable_market | String | 50 | YES | NULL | Market this applies to |
| applicable_strategy | String | 50 | YES | NULL | Strategy this applies to |
| confidence_score | Float | — | NO | 0.75 | Confidence in this insight (0.0-1.0) |
| supporting_evidence | String | 1000 | YES | NULL | Why we're confident (e.g., "Based on 5 recent deals, all within range") |
| created_at | DateTime | — | NO | NOW() | When insight was extracted |

### Rationale

- **insight_text:** Natural language summary for humans
- **structured_value_json:** Enables programmatic use (future AI/algorithms)
- **supporting_evidence:** Explains the confidence score
- **applicable_market + strategy:** Enables precise recommendation matching
- **Higher confidence_score than parent item:** Insights are more refined than raw knowledge

### Example Records

```
1. knowledge_item_id: 101
   insight_text: "For wholesale deals in Memphis, assume $28-32k bathroom rehab"
   structured_value_json: {
     "low": 28000,
     "high": 32000,
     "median": 30000,
     "category": "bathroom"
   }
   applicable_market: "memphis"
   applicable_strategy: "wholesale"
   confidence_score: 0.92
   supporting_evidence: "Based on 5 recent wholesale deals, all within range"

2. knowledge_item_id: 102
   insight_text: "Sellers in Memphis typically accept 3-5% below asking price"
   structured_value_json: {
     "discount_pct_low": 0.03,
     "discount_pct_high": 0.05,
     "discount_pct_typical": 0.04
   }
   applicable_market: "memphis"
   confidence_score: 0.75
   supporting_evidence: "10-deal sample, 80% hit this range"
```

---

## 4. OutcomeFeedback

**Purpose:** Record actual vs. predicted results for learning

### Fields

| Field | Type | Size | Nullable | Default | Purpose |
|-------|------|------|----------|---------|---------|
| id | UUID/Serial | — | NO | PK | Primary key |
| case_id | String | 50 | YES | NULL | Reference to ExecutionCase (external) |
| deal_id | String | 50 | YES | NULL | Deal identifier for reference |
| market | String | 50 | NO | — | Market where deal occurred |
| strategy | String | 50 | NO | — | Strategy used |
| asset_type | String | 50 | YES | NULL | Asset type |
| predicted_result_json | JSON | — | YES | NULL | What was predicted (ARV, rehab, profit, etc.) |
| actual_result_json | JSON | — | YES | NULL | What actually happened |
| delta_json | JSON | — | YES | NULL | Difference (calculated field) |
| lesson_text | Text | — | YES | NULL | Extracted lesson from mismatch |
| confidence_adjustment | Float | — | YES | 0.0 | How much to adjust confidence on similar future cases (-1.0 to +1.0) |
| created_at | DateTime | — | NO | NOW() | When feedback recorded |

### Rationale

- **case_id + deal_id:** Link to operational outcome without importing execution models
- **market + strategy + asset_type:** Enable filtering by context
- **predicted_result_json:** Store full prediction for audit
- **actual_result_json:** Store full actual results
- **delta_json:** Calculated differences (easy querying)
- **lesson_text:** Human-extracted learning point
- **confidence_adjustment:** Guides future confidence scoring

### Example Records

```
1. case_id: "CASE_123"
   deal_id: "DEAL_2026_04_001"
   market: "memphis"
   strategy: "wholesale"
   asset_type: "single_family"
   predicted_result_json: {
     "estimated_arv": 185000,
     "estimated_rehab": 30000,
     "estimated_profit": 15000,
     "confidence": 0.85
   }
   actual_result_json: {
     "actual_arv": 188000,
     "actual_rehab": 35000,
     "actual_profit": 8000,
     "deal_days": 28
   }
   delta_json: {
     "arv_delta": 3000,
     "arv_delta_pct": 0.016,
     "rehab_delta": 5000,
     "rehab_delta_pct": 0.167,
     "profit_delta": -7000,
     "profit_delta_pct": -0.467
   }
   lesson_text: "Rehab estimates underestimated by 17%; adjust baseline +15%"
   confidence_adjustment: -0.08

2. case_id: "CASE_124"
   deal_id: "DEAL_2026_04_002"
   market: "nashville"
   strategy: "hold"
   predicted_result_json: {
     "estimated_cap_rate": 0.048,
     "estimated_annual_income": 9600
   }
   actual_result_json: {
     "actual_cap_rate": 0.051,
     "actual_annual_income": 10200
   }
   delta_json: {
     "cap_rate_delta": 0.003,
     "cap_rate_delta_pct": 0.063,
     "income_delta": 600
   }
   lesson_text: "Conservative estimate; market performing better than expected"
   confidence_adjustment: +0.05
```

---

## 5. DecisionMemory

**Purpose:** Historic record of what was recommended, decided, and the outcome

### Fields

| Field | Type | Size | Nullable | Default | Purpose |
|-------|------|------|----------|---------|---------|
| id | UUID/Serial | — | NO | PK | Primary key |
| subject_type | String | 100 | NO | — | What is being tracked (e.g., "rehab_budget", "strategy_selection") |
| subject_id | String | 255 | YES | NULL | Specific ID (e.g., "memphis_wholesale_sf") |
| market | String | 50 | NO | — | Market context |
| strategy | String | 50 | YES | NULL | Strategy context |
| recommendation_text | String | 1000 | NO | — | What was recommended |
| decision_taken | String | 1000 | YES | NULL | What was actually decided |
| outcome_score | Float | — | YES | NULL | How well it turned out (-1.0 to +1.0) |
| lesson_text | Text | — | YES | NULL | What we learned |
| created_at | DateTime | — | NO | NOW() | When recorded |
| updated_at | DateTime | — | NO | NOW() | Last update with outcome |

### Rationale

- **subject_type + subject_id:** Enable any type of decision tracking
- **recommendation_text + decision_taken:** Compare what was advised vs. done
- **outcome_score:** Quantify result quality
- **lesson_text:** Extract and store learning
- **Queryable by market + strategy:** Enable "what works in this context" analysis

### Example Records

```
1. subject_type: "rehab_budget"
   subject_id: "memphis_wholesale_sf"
   market: "memphis"
   strategy: "wholesale"
   recommendation_text: "Assume $30,000 budget"
   decision_taken: "Used $30,000 budget"
   outcome_score: -0.17  // Was 17% too low (actual $35k)
   lesson_text: "Need to increase baseline by 15% based on 5-deal pattern"

2. subject_type: "strategy_selection"
   subject_id: "deal_2026_04_001"
   market: "memphis"
   recommendation_text: "Recommend wholesale strategy (margin > 15%)"
   decision_taken: "Pursued wholesale strategy"
   outcome_score: +0.08  // Beat projection slightly
   lesson_text: "Wholesale remains effective in Memphis; maintain strategy"

3. subject_type: "seller_willingness"
   subject_id: "foreclosure_properties"
   market: "nashville"
   recommendation_text: "Expect 5-8% price reduction on second offer"
   decision_taken: "Listed 6% below asking"
   outcome_score: -0.10  // Seller held firm; negotiation took longer
   lesson_text: "Foreclosure sellers more rigid than expected; try different angle"
```

---

## Model Relationships Diagram

```
┌──────────────────────┐
│  KnowledgeSource     │
├──────────────────────┤
│ id (PK)              │
│ source_name          │
│ source_type          │
│ trust_level          │
│ market               │
│ active               │
└──────────────────────┘
        │
        │ (1:Many)
        │
        ↓
┌──────────────────────┐
│  KnowledgeItem       │
├──────────────────────┤
│ id (PK)              │
│ source_id (FK above) │
│ title                │
│ knowledge_type       │
│ market               │
│ strategy (array)     │
│ confidence_score     │
│ status               │
└──────────────────────┘
        │
        │ (1:Many)
        │
        ↓
┌──────────────────────┐
│ KnowledgeInsight     │
├──────────────────────┤
│ id (PK)              │
│ knowledge_item_id    │
│ (FK above)           │
│ insight_text         │
│ structured_value     │
│ confidence_score     │
└──────────────────────┘


┌──────────────────────────┐
│  ExecutionCase           │  (EXTERNAL)
│ (in execution layer)     │  (NOT modified)
└──────────────────────────┘
        │
        │ (reference only)
        │
        ↓
┌──────────────────────────┐
│  OutcomeFeedback         │
├──────────────────────────┤
│ id (PK)                  │
│ case_id (text ref)       │
│ deal_id (text ref)       │
│ market                   │
│ strategy                 │
│ predicted_result_json    │
│ actual_result_json       │
│ delta_json (calculated)  │
│ lesson_text              │
│ confidence_adjustment    │
└──────────────────────────┘
        │
        │ (updates)
        │
        ↓
┌──────────────────────────┐
│  DecisionMemory          │
├──────────────────────────┤
│ id (PK)                  │
│ subject_type             │
│ subject_id               │
│ market                   │
│ strategy                 │
│ recommendation_text      │
│ decision_taken           │
│ outcome_score            │
│ lesson_text              │
└──────────────────────────┘
```

---

## Code Structure Reference

### Where These Models Go (Phase 1 vs. Later)

**Phase 1 (Now):** Code Stubs in Pydantic Schemas Only
```
app/schemas/heimdall_intelligence.py
  - KnowledgeSourceCreate
  - KnowledgeSourceOut
  - KnowledgeItemCreate
  - KnowledgeItemOut
  - KnowledgeInsightCreate
  - KnowledgeInsightOut
  - OutcomeFeedbackCreate
  - OutcomeFeedbackOut
  - DecisionMemoryOut
```

**Phase 2 (Later, Optional):** SQLAlchemy ORM Models + Migrations
```
app/models/heimdall_intelligence.py
  - HeimdallKnowledgeSource
  - HeimdallKnowledgeItem
  - HeimdallKnowledgeInsight
  - HeimdallOutcomeFeedback
  - HeimdallDecisionMemory

alembic/versions/
  - 0XXX_create_heimdall_tables.py (optional, deferred)
```

---

## Database Table Definitions (Reference Only - Not Applied Yet)

### If we chose PostgreSQL (post-Phase 1):

```sql
-- KnowledgeSource
CREATE TABLE heimdall_knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_url VARCHAR(1024),
    jurisdiction VARCHAR(10),
    market VARCHAR(50),
    category VARCHAR(100),
    trust_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- KnowledgeItem  
CREATE TABLE heimdall_knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES heimdall_knowledge_sources(id),
    title VARCHAR(500) NOT NULL,
    content_raw TEXT,
    content_summary TEXT,
    knowledge_type VARCHAR(50) NOT NULL,
    market VARCHAR(50),
    strategy JSONB,
    asset_type VARCHAR(50),
    tags_json JSONB,
    confidence_score FLOAT NOT NULL DEFAULT 0.5,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- Similar for KnowledgeInsight, OutcomeFeedback, DecisionMemory
-- (Deferred - documented in optional DB plan)
```

---

## Validation Rules

### KnowledgeSource
- ✅ source_name: required, 1-255 chars
- ✅ source_type: required, must be in enum
- ✅ trust_level: required, must be high|medium|low
- ✅ One record per unique source

### KnowledgeItem
- ✅ source_id: required, must exist
- ✅ title: required, 1-500 chars
- ✅ knowledge_type: required, must be in enum
- ✅ confidence_score: 0.0-1.0
- ✅ strategy: if provided, must be array of valid strategy names

### KnowledgeInsight
- ✅ knowledge_item_id: required, must exist
- ✅ insight_text: required, 1-1000 chars
- ✅ confidence_score: 0.0-1.0

### OutcomeFeedback
- ✅ market: required
- ✅ strategy: required
- ✅ predicted_result_json: must be valid JSON if provided
- ✅ actual_result_json: must be valid JSON if provided

### DecisionMemory
- ✅ subject_type: required
- ✅ market: required
- ✅ recommendation_text: required

---

## Query Patterns (Preview of Service Layer)

```python
# Find high-confidence insights for a strategy
insights = db.query(KnowledgeInsight)
    .join(KnowledgeItem)
    .filter(
        KnowledgeItem.market == "memphis",
        KnowledgeItem.strategy.contains("wholesale"),
        KnowledgeInsight.confidence_score >= 0.75
    )
    .all()

# Get recent outcomes for a market
outcomes = db.query(OutcomeFeedback)
    .filter(
        OutcomeFeedback.market == "nashville",
        OutcomeFeedback.created_at >= (now - 30 days)
    )
    .order_by(OutcomeFeedback.created_at.desc())
    .all()

# Find decision memory by subject
decisions = db.query(DecisionMemory)
    .filter(
        DecisionMemory.subject_type == "rehab_budget",
        DecisionMemory.market == "memphis",
        DecisionMemory.strategy == "wholesale"
    )
    .all()
```

---

## Summary

**What This Model Enables:**

✅ Knowledge ingestion from multiple sources  
✅ Confidence-scored insights for recommendations  
✅ Outcome tracking for learning validation  
✅ Decision historical records for analysis  
✅ Zero impact on execution layer  
✅ Future-proof for ML/AI integration  
✅ Non-breaking implementation strategy  

**Next Phase:**

→ Phase 3: Create Constants/Enums (SAFE, producible now)
