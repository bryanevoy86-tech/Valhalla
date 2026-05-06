# Heimdall Intelligence Layer V1 — Route Plan

**Status:** Design Document  
**Created:** 2026-04-13  
**Purpose:** Define all endpoints for knowledge ingestion, discovery, and outcome recording.

---

## Route Overview

**Base Path:** `/heimdall/intelligence`  
**Auth:** Inherited from main app auth (if present)  
**Response Format:** JSON  
**Status Codes:** Standard REST (200, 201, 400, 404, 422, 500)  

**Total Endpoints:** 9 core routes

---

## Route Catalog

### 1. Knowledge Sources — Register & List

#### POST `/heimdall/intelligence/sources`

**Purpose:** Register a new knowledge source  
**Access:** Requires knowledge management role (or admin)  
**Request:**

```json
{
  "source_name": "string (required)",
  "source_type": "string (required)",
  "source_url": "string (optional)",
  "jurisdiction": "string (optional, e.g., 'TN', 'US')",
  "market": "string (optional, e.g., 'memphis', 'nashville')",
  "category": "string (optional, e.g., 'market_trends', 'legal')",
  "trust_level": "string (required: 'high'|'medium'|'low')",
  "active": "boolean (default: true)"
}
```

**Response:**

```json
{
  "id": 42,
  "source_name": "Memphis Market Report Q1 2026",
  "source_type": "market_report",
  "source_url": "https://...",
  "jurisdiction": "TN",
  "market": "memphis",
  "category": "market_trends",
  "trust_level": "high",
  "active": true,
  "created_at": "2026-04-13T10:30:00Z",
  "knowledge_items_count": 0
}
```

**Errors:**
- 422: Invalid source_type or trust_level
- 400: Missing required fields

---

#### GET `/heimdall/intelligence/sources`

**Purpose:** List all registered knowledge sources  
**Query Parameters:**
```
?market=memphis
?trust_level=high
?active=true
?limit=50
?offset=0
```

**Response:**

```json
{
  "total": 23,
  "limit": 50,
  "offset": 0,
  "sources": [
    {
      "id": 42,
      "source_name": "Memphis Market Report Q1 2026",
      "source_type": "market_report",
      "trust_level": "high",
      "market": "memphis",
      "active": true,
      "created_at": "2026-04-13T10:30:00Z",
      "knowledge_items_count": 5,
      "last_item_added": "2026-04-13T11:45:00Z"
    },
    ...
  ]
}
```

**Errors:**
- 400: Invalid filter parameters

---

### 2. Knowledge Items — Ingest & Retrieve

#### POST `/heimdall/intelligence/items`

**Purpose:** Ingest a new piece of knowledge  
**Requires:** source_id must exist  
**Request:**

```json
{
  "source_id": 42,
  "title": "string (required)",
  "content_raw": "string (required, full text)",
  "content_summary": "string (optional, short summary)",
  "knowledge_type": "string (required: see KnowledgeType enum)",
  "market": "string (optional, e.g., 'memphis')",
  "strategy": ["array of strategy strings (optional)"],
  "asset_type": "string (optional, e.g., 'single_family', 'multifamily')",
  "tags_json": ["array of tags (optional)"],
  "confidence_score": "float (0.0-1.0, optional, default 0.5)"
}
```

**Response:**

```json
{
  "id": 101,
  "source_id": 42,
  "title": "Average Rehab Cost Q1 2026",
  "content_raw": "Full text from source...",
  "content_summary": "Bathroom rehabs $26-32k, kitchen $35-45k",
  "knowledge_type": "rehab_cost",
  "market": "memphis",
  "strategy": ["wholesale", "flip"],
  "asset_type": "single_family",
  "tags_json": ["cost_driven", "seasonal"],
  "confidence_score": 0.85,
  "status": "draft",
  "created_at": "2026-04-13T11:00:00Z",
  "updated_at": "2026-04-13T11:00:00Z",
  "insights_count": 0
}
```

**Errors:**
- 404: source_id not found
- 422: Invalid knowledge_type or strategy value
- 400: Missing required fields

---

#### GET `/heimdall/intelligence/items`

**Purpose:** List knowledge items with filtering  
**Query Parameters:**
```
?source_id=42
?market=memphis
?strategy=wholesale
?asset_type=single_family
?knowledge_type=rehab_cost
?status=draft|reviewed|trusted|deprecated|rejected
?min_confidence=0.75
?limit=50
?offset=0
```

**Response:**

```json
{
  "total": 128,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": 101,
      "source_id": 42,
      "source_name": "Memphis Market Report Q1 2026",
      "title": "Average Rehab Cost Q1 2026",
      "content_summary": "Bathroom rehabs $26-32k, kitchen $35-45k",
      "knowledge_type": "rehab_cost",
      "market": "memphis",
      "strategy": ["wholesale", "flip"],
      "asset_type": "single_family",
      "confidence_score": 0.85,
      "status": "trusted",
      "created_at": "2026-04-13T11:00:00Z",
      "insights_count": 2
    },
    ...
  ]
}
```

**Errors:**
- 400: Invalid filter parameters

---

#### GET `/heimdall/intelligence/items/{item_id}`

**Purpose:** Retrieve full detail of a single knowledge item  

**Response:**

```json
{
  "id": 101,
  "source_id": 42,
  "source_name": "Memphis Market Report Q1 2026",
  "title": "Average Rehab Cost Q1 2026",
  "content_raw": "Full text from source...",
  "content_summary": "Bathroom rehabs $26-32k, kitchen $35-45k",
  "knowledge_type": "rehab_cost",
  "market": "memphis",
  "strategy": ["wholesale", "flip"],
  "asset_type": "single_family",
  "tags_json": ["cost_driven", "seasonal", "labor_intensive"],
  "confidence_score": 0.85,
  "status": "trusted",
  "created_at": "2026-04-13T11:00:00Z",
  "updated_at": "2026-04-13T11:00:00Z",
  "insights": [
    {
      "id": 201,
      "insight_text": "For wholesale deals in Memphis, assume $28-32k bathroom rehab",
      "confidence_score": 0.90,
      "created_at": "2026-04-13T11:15:00Z"
    },
    ...
  ]
}
```

**Errors:**
- 404: item_id not found

---

### 3. Knowledge Insights — Extract & Score

#### POST `/heimdall/intelligence/items/{item_id}/insights`

**Purpose:** Extract structured insight from knowledge item  
**Requires:** item_id must exist  
**Request:**

```json
{
  "insight_text": "string (required)",
  "structured_value_json": "object (optional, structured data)",
  "applicable_market": "string (optional)",
  "applicable_strategy": "string (optional)",
  "confidence_score": "float (0.0-1.0, optional, default 0.75)"
}
```

**Response:**

```json
{
  "id": 201,
  "knowledge_item_id": 101,
  "insight_text": "For wholesale deals in Memphis, assume $28-32k bathroom rehab",
  "structured_value_json": {
    "low": 28000,
    "high": 32000,
    "median": 30000,
    "category": "bathroom"
  },
  "applicable_market": "memphis",
  "applicable_strategy": "wholesale",
  "confidence_score": 0.90,
  "created_at": "2026-04-13T11:15:00Z"
}
```

**Errors:**
- 404: item_id not found
- 400: Missing required fields

---

#### GET `/heimdall/intelligence/items/{item_id}/insights`

**Purpose:** List insights for a knowledge item  

**Response:**

```json
{
  "knowledge_item_id": 101,
  "total": 2,
  "insights": [
    {
      "id": 201,
      "insight_text": "For wholesale deals in Memphis, assume $28-32k bathroom rehab",
      "structured_value_json": {...},
      "applicable_market": "memphis",
      "applicable_strategy": "wholesale",
      "confidence_score": 0.90,
      "created_at": "2026-04-13T11:15:00Z"
    },
    ...
  ]
}
```

---

### 4. Search Knowledge

#### POST `/heimdall/intelligence/search`

**Purpose:** Search knowledge base with multiple filters  
**Request:**

```json
{
  "market": "string (optional)",
  "strategy": "string (optional)",
  "asset_type": "string (optional)",
  "knowledge_types": ["array (optional)"],
  "keywords": "string (optional, free text search)",
  "min_confidence": "float (optional, default 0.75)",
  "limit": "integer (optional, default 20)"
}
```

**Response:**

```json
{
  "query": {
    "market": "nashville",
    "strategy": "wholesale",
    "keywords": "rehab cost"
  },
  "total_results": 8,
  "results": [
    {
      "knowledge_item_id": 101,
      "title": "Average Rehab Cost Q1 2026",
      "content_summary": "Bathroom rehabs $26-32k...",
      "knowledge_type": "rehab_cost",
      "market": "nashville",
      "strategy": "wholesale",
      "confidence_score": 0.88,
      "source_name": "Memphis Market Report Q1 2026",
      "source_trust_level": "high",
      "insights_available": 2,
      "created_at": "2026-04-13T11:00:00Z",
      "relevance_score": 0.95
    },
    ...
  ]
}
```

**Errors:**
- 400: Invalid filter parameters

---

### 5. Get Recommendations

#### POST `/heimdall/intelligence/recommend`

**Purpose:** Get data-backed recommendations for strategy/market context  
**Request:**

```json
{
  "market": "string (required)",
  "strategy": "string (required)",
  "asset_type": "string (optional)",
  "question": "string (optional, natural language query)",
  "context": "object (optional, additional context)"
}
```

**Response:**

```json
{
  "market": "nashville",
  "strategy": "wholesale",
  "asset_type": "single_family",
  "question": "What should we assume for rehab costs?",
  "recommendation": "Assume $26-32k rehab budget",
  "confidence": 0.88,
  "supporting_evidence": [
    {
      "text": "Nashville Market Report Q1 2026",
      "type": "source",
      "trust_level": "high",
      "relevance": 0.95
    },
    {
      "text": "3 of last 5 recent wholesale deals hit mid-range",
      "type": "outcome_feedback",
      "relevance": 0.87
    }
  ],
  "caveats": [
    "Commercial properties may vary by 10-15%",
    "Minor cosmetic rehabs historically underestimated"
  ],
  "last_updated": "2026-04-13",
  "advisory_only": true
}
```

**Errors:**
- 400: Missing required fields
- 404: No recommendations available for this market/strategy

---

### 6. Record Outcome Feedback

#### POST `/heimdall/intelligence/outcomes`

**Purpose:** Record actual vs. predicted outcome after execution  
**Request:**

```json
{
  "case_id": "string (optional, execution case ID)",
  "deal_id": "string (optional, deal identifier)",
  "market": "string (required)",
  "strategy": "string (required)",
  "predicted_result_json": "object (optional, what was predicted)",
  "actual_result_json": "object (optional, what happened)",
  "notes": "string (optional)"
}
```

**Response:**

```json
{
  "id": 301,
  "case_id": "CASE_123",
  "deal_id": "DEAL_2026_04_001",
  "market": "nashville",
  "strategy": "wholesale",
  "predicted_result_json": {
    "estimated_arv": 185000,
    "estimated_rehab": 30000,
    "estimated_profit": 15000
  },
  "actual_result_json": {
    "actual_arv": 188000,
    "actual_rehab": 35000,
    "actual_profit": 8000
  },
  "delta_json": {
    "arv_delta": 3000,
    "rehab_delta": 5000,
    "profit_delta": -7000
  },
  "created_at": "2026-04-13T14:30:00Z"
}
```

**Errors:**
- 400: Missing required fields
- 422: Invalid market or strategy

---

#### GET `/heimdall/intelligence/outcomes`

**Purpose:** List recorded outcome feedback  
**Query Parameters:**
```
?market=nashville
?strategy=wholesale
?limit=20
?offset=0
```

**Response:**

```json
{
  "total": 45,
  "limit": 20,
  "offset": 0,
  "outcomes": [
    {
      "id": 301,
      "case_id": "CASE_123",
      "deal_id": "DEAL_2026_04_001",
      "market": "nashville",
      "strategy": "wholesale",
      "profit_delta": -7000,
      "created_at": "2026-04-13T14:30:00Z"
    },
    ...
  ]
}
```

---

#### POST `/heimdall/intelligence/outcomes/{outcome_id}/lesson`

**Purpose:** Generate and store lesson from outcome  
**Request:**

```json
{
  "lesson_text": "string (required)",
  "applies_to": {
    "market": "string (optional)",
    "strategy": "string (optional)",
    "asset_type": "string (optional)"
  },
  "confidence_score": "float (0.0-1.0, optional)"
}
```

**Response:**

```json
{
  "id": 401,
  "outcome_id": 301,
  "lesson_text": "Rehab estimates need +15% adjustment for Nashville wholesale",
  "applies_to": {
    "market": "nashville",
    "strategy": "wholesale",
    "asset_type": "single_family"
  },
  "confidence_score": 0.82,
  "created_at": "2026-04-13T14:45:00Z"
}
```

**Errors:**
- 404: outcome_id not found
- 400: Missing lesson_text

---

### 7. Get Market Memory Snapshot

#### GET `/heimdall/intelligence/market-memory`

**Purpose:** Get aggregated market insights and performance summary  
**Query Parameters:**
```
?market=nashville
?strategy=wholesale
?asset_type=single_family
?days=30
```

**Response:**

```json
{
  "market": "nashville",
  "strategy": "wholesale",
  "asset_type": "single_family",
  "generated_at": "2026-04-13T15:00:00Z",
  "primary_insights": [
    {
      "title": "Rehab Cost Baseline",
      "value": "$34,500",
      "confidence": 0.88,
      "last_updated": "2026-04-13",
      "data_points": 5,
      "source": "Recent outcomes + market reports"
    },
    {
      "title": "Target ARV Accuracy",
      "value": "98%",
      "confidence": 0.75,
      "trend": "+2% vs 30 days ago"
    },
    {
      "title": "Avg Days to Close",
      "value": "32 days",
      "confidence": 0.80,
      "data_points": 8
    }
  ],
  "recent_outcomes": [
    {
      "deal_date": "2026-04-12",
      "deal_id": "DEAL_2026_04_010",
      "profit_delta": 2000,
      "profit_delta_pct": 1.2,
      "lesson": "Strong buyer interest shortens close timeline"
    },
    ...
  ],
  "summary": {
    "total_knowledge_items": 42,
    "total_outcomes_tracked": 23,
    "overall_confidence": 0.84,
    "knowledge_sources": 8,
    "last_updated": "2026-04-13T14:45:00Z"
  }
}
```

**Errors:**
- 400: Invalid query parameters
- 404: No market memory available for this market/strategy

---

## Route Implementation Strategy

### Priority Order (Phase 1)

| Priority | Route | Complexity | Impl Est |
|----------|-------|-----------|---------|
| P0 | POST /sources | Low | 0.5h |
| P0 | POST /items | Low | 0.5h |
| P0 | POST /outcomes | Low | 0.5h |
| P1 | GET /sources | Medium | 0.5h |
| P1 | GET /items | Medium | 0.5h |
| P1 | GET /items/{id} | Low | 0.25h |
| P1 | POST /items/{id}/insights | Low | 0.5h |
| P2 | POST /search | High | 1h |
| P2 | POST /recommend | High | 1.5h |
| P3 | GET /market-memory | High | 1.5h |

**Total Estimated Implementation Time: ~8 hours**

---

## Error Handling Pattern

All endpoints follow this pattern:

```json
{
  "status": "error",
  "status_code": 422,
  "error_type": "validation_error",
  "message": "Invalid source_type",
  "details": {
    "field": "source_type",
    "received": "unknown_source",
    "valid_options": ["government", "public_web", "forum", ...]
  }
}
```

---

## Authentication & Authorization (Deferred to Main App)

Phase 1 assumes:
- Auth middleware inherited from main FastAPI app
- All users can read knowledge
- Knowledge management role required for write operations (TBD)
- No complex RBAC (keep it simple)

---

## Testing Strategy

### Per Endpoint:
✅ Test happy path (valid request → 200/201)  
✅ Test error paths (invalid request → 400/422)  
✅ Test not found (missing resource → 404)  
✅ Test filtering/search accuracy  
✅ Test response schema correctness  

### E2E Flow:
✅ Register source → Add item → Extract insight → Search → Recommend  
✅ Record outcome → Generate lesson → Update market memory  
✅ List endpoints with filters + pagination  

---

## Deployment Safety

✅ All routes isolated to `/hemdalll/intelligence` prefix  
✅ No modifications to existing execution routes  
✅ No database migrations required (can use in-memory or optional DB)  
✅ Can be disabled by removing router registration (clean rollback)  
✅ Zero dependencies on execution layer  

---

## Next Phase

→ Phase 2: Core Data Model Documentation + Code Stubs
