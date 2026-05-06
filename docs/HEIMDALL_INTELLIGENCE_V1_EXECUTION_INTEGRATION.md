# Heimdall Intelligence Layer V1 — Execution Integration (Future)

**Status:** Design Document (Future Integration Plan)  
**Created:** 2026-04-13  
**Purpose:** Document how Heimdall will eventually enhance execution layer WITHOUT breaking it now.

---

## Executive Summary

**Phase 1 (NOW):** Heimdall Intelligence is completely isolated from Execution layer
- Zero dependencies
- Zero modifications to execution routes
- Optional bridge helpers (discussed below)
- Safe to run alongside execution without interference

**Phase 2+ (POST-WEWEB):** Gradual, opt-in integration
- Execution records outcome feedback to Heimdall
- Heimdall provides advisory context for execution decisions
- Execution layer remains primary decision-maker
- No autonomous behavior changes

**Timeline:** Execution layer unchanged through first WeWeb launch. Integration starts after stable operations (Month 1+).

---

## Current Architecture (Phase 1: Isolated)

```
┌────────────────────────────────────────┐
│        EXECUTION LAYER (LIVE)          │
│  - Cases, decisions, outcomes          │
│  - No Heimdall dependency              │
│  - No Heimdall data flow               │
└────────────────────────────────────────┘
                    ↓ (NO CONNECTION)
┌────────────────────────────────────────┐
│   HEIMDALL INTELLIGENCE (ISOLATED)     │
│  - Knowledge sources, items, insights  │
│  - Outcomes (manual or future)         │
│  - Completely independent              │
└────────────────────────────────────────┘
```

**Guarantee:** Execution layer works exactly as-is. Heimdall is pure addition.

---

## Phase 1: Optional Bridge Helpers (Safe)

For teams wanting early integration, safe helper functions in:

```
app/services/heimdall_intelligence_bridge.py
```

These helpers are **advisory only** and don't modify execution behavior:

### 1. get_market_insights_for_strategy

```python
def get_market_insights_for_strategy(
    market: str,
    strategy: str,
    asset_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get high-confidence insights for a market/strategy combo.
    
    Returns insights for human context (not auto-decision).
    Returns empty dict if no data.
    
    Usage: Optional contextual display in execution UI
    """
```

**Non-Breaking:** Returns None/empty if no data; never blocks execution.

### 2. get_recent_lessons_for_market

```python
def get_recent_lessons_for_market(
    market: str,
    days: int = 30
) -> List[str]:
    """
    Get recent lessons learned for a market.
    
    Returns list of lesson texts from outcomes.
    Useful for team context/training.
    
    Usage: Optional team briefing display
    """
```

**Non-Breaking:** Informational only; never modifies execution.

### 3. get_knowledge_hints_for_case

```python
def get_knowledge_hints_for_case(
    case: ExecutionCase,
) -> Dict[str, Any]:
    """
    Get applicable knowledge hints for a case context.
    
    Given case market, strategy, asset type,
    returns relevant knowledge items.
    
    Usage: Optional sidebar/collateral display in case detail
    """
```

**Non-Breaking:** Hints for human operators; doesn't override decision logic.

---

## Bridge Layer Implementation Strategy

### File: app/services/heimdall_intelligence_bridge.py

```python
"""
Safe bridge between Heimdall Intelligence and Execution layers.

IMPORTANT CONSTRAINTS:
- NO modifications to execution case data
- NO auto-decisions or logic changes
- NO side effects (pure advisory functions)
- All functions optional to call
- All functions safe to remove without breaking execution
"""

from typing import Optional, Dict, Any
from app.services.heimdall_intelligence_service import get_service
from app.models.execution_case import ExecutionCase  # Import only if needed


def get_market_insights_for_strategy(
    market: str,
    strategy: str,
    asset_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Advisory function: Get insights for human context.
    NEVER called automatically; only if explicitly requested.
    """
    try:
        service = get_service()
        # Query for high-confidence insights
        search_params = {
            "market": market,
            "strategy": strategy,
            "min_confidence": 0.8,
            "limit": 5,
        }
        result = service.search_knowledge(search_params)
        
        # Format for UI/context
        return {
            "applicable_knowledge": result.get("results", []),
            "confidence_threshold": 0.8,
            "advisory_only": True,
        }
    except Exception:
        # Safe to fail - return empty context
        return {"applicable_knowledge": [], "advisory_only": True}


def get_recent_lessons_for_market(
    market: str,
    days: int = 30
) -> List[str]:
    """
    Advisory function: Get recent lessons learned.
    For team context/training, not decisions.
    """
    try:
        service = get_service()
        # Get recent outcomes and extract lessons
        outcomes = [
            o for o in service.outcomes.values()
            if o.get("market") == market and o.get("lesson_text")
        ]
        
        return [o["lesson_text"] for o in outcomes if o.get("lesson_text")]
    except Exception:
        return []


def get_knowledge_hints_for_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advisory function: Get knowledge hints for a case.
    Enriches case context for human operator.
    """
    try:
        service = get_service()
        market = case.get("market")
        strategy = case.get("strategy")
        asset_type = case.get("asset_type")
        
        if not market or not strategy:
            return {"hints": [], "error": "Missing case context"}
        
        # Get applicable knowledge
        hints = []
        
        # Get insights for the strategy
        search_result = service.search_knowledge({
            "market": market,
            "strategy": strategy,
            "min_confidence": 0.7,
            "limit": 3,
        })
        
        hints.extend(search_result.get("results", []))
        
        # Get recent lessons for this market
        lessons = get_recent_lessons_for_market(market)
        
        return {
            "hints": hints,
            "lessons": lessons,
            "for_case_id": case.get("id"),
            "advisory_only": True,
        }
    except Exception as e:
        return {"hints": [], "error": str(e), "advisory_only": True}


# NO automatic integration
# NO outcome recording without explicit call
# NO decision modification
```

---

## Phase 2+ Integration Plan (POST-WEWEB)

### Milestone 1: Outcome Recording (Week 3-4)

After execution layer stabilizes:

**Define:**
```python
# In execution service
def record_execution_outcome(case_id: str, execution_result: Dict):
    """
    After case closes, operator can manually call this.
    Records outcome to Heimdall for learning.
    """
    # Get case details
    case = get_case(case_id)
    
    # Call Heimdall to record
    from app.services.heimdall_intelligence_bridge import record_case_outcome
    record_case_outcome(case, execution_result)
```

**Process:**
1. Operator closes case in execution UI
2. Optional checkbox: "Record outcome for learning?"
3. If yes, calls Heimdall outcome recording
4. Heimdall stores predicted vs actual
5. Later generates lesson

**Non-Breaking:** Completely optional, no forcing.

### Milestone 2: Advisory Enrichment (Month 1+)

Enrich execution UI with optional Heimdall context:

```python
# In execution routes (OPTIONAL)
@router.get("/cases/{case_id}")
async def get_case_detail(case_id: str):
    case = get_case(case_id)
    
    # EXISTING execution data
    response = CaseDetailOut.from_orm(case)
    
    # NEW (optional): Add Heimdall context
    try:
        from app.services.heimdall_intelligence_bridge import get_knowledge_hints_for_case
        hints = get_knowledge_hints_for_case(case.dict())
        response.heimdall_context = hints  # Optional field
    except:
        pass  # Gracefully fail if Heimdall not available
    
    return response
```

**Impact:** UI shows additional context. Case processing unchanged.

### Milestone 3: Confidence Scoring Improvement (Month 2+)

Use Heimdall data to improve risk scoring:

```python
# In execution risk calculation
def calculate_risk_score(case: ExecutionCase) -> float:
    base_score = current_calculation_logic(case)  # Existing
    
    # Improvement: Consider Heimdall confidence adjustments
    try:
        from app.services.heimdall_intelligence_bridge import get_confidence_adjustment
        adj = get_confidence_adjustment(
            case.market,
            case.strategy,
            case.estimated_profit
        )
        # Apply as modifier, not replacement
        base_score = base_score * (1.0 + adj)
    except:
        pass  # Failsafe: use base score if Heimdall unavailable
    
    return base_score
```

**Important:** Fails safely; never blocks execution.

### Milestone 4: Request Enrichment (Month 3+)

Populate next-action and task generation with Heimdall insights:

```python
# In execution task generation
def generate_next_action(case: ExecutionCase) -> str:
    # Existing logic
    base_action = current_action_logic(case)
    
    # Enhancement: Add Heimdall context
    try:
        from app.services.heimdall_intelligence_bridge import get_action_hints
        hints = get_action_hints(case)
        if hints:
            # Enhance description with insights
            base_action.description += f"\n\nNote: {hints}"
    except:
        pass  # Fallback to base action
    
    return base_action
```

**Non-Breaking:** Adds context to existing actions; doesn't change logic.

---

## What Heimdall WILL Eventually Improve

✅ **Risk Scoring** — More data points, historical pattern matching  
✅ **Strategy Selection** — Market/case data to support better choices  
✅ **Next-Action Recommendations** — Based on similar past cases  
✅ **Task Generation** — Predictive tasks based on outcomes  
✅ **Outcome Accuracy** — Better predictions from historical data  
✅ **Team Learning** — Centralized lessons and patterns  
✅ **Market Memory** — Institutional knowledge retention  

---

## What Heimdall Will NOT Change

❌ **Execution Flow** — Same 7 routes, same endpoints  
❌ **Case Processing** — Same business logic  
❌ **Decision Authority** — Humans remain decision-makers  
❌ **Web3/Scraping** — No autonomous internet activity  
❌ **LLM Automation** — No autonomous recommendations  
❌ **Existing Data** — No modifications to existing cases  

---

## Backwards Compatibility Guarantee

**Phase 1 (Now):**
- ✅ Execution layer unchanged
- ✅ Heimdall is optional
- ✅ Bridge functions are optional
- ✅ Zero breaking changes
- ✅ Can disable Heimdall router without affecting execution

**Phase 2+ (Later):**
- ✅ Execution logic remains primary
- ✅ Heimdall is advisory
- ✅ Bridge functions are optional to call
- ✅ All integration is graceful fallback
- ✅ Can disable/remove Heimdall anytime

---

## Error Handling & Safety

All bridge functions must follow this pattern:

```python
def bridge_function(...):
    try:
        # Try to get Heimdall context
        service = get_service()
        result = # ... Heimdall operation
        return result
    except Exception as e:
        # Log but don't fail execution
        logger.warning(f"Heimdall context unavailable: {e}")
        # Return safe default/empty
        return None  # or {} or [] as appropriate
    
    # NEVER raise exception
    # NEVER modify execution case
    # NEVER block execution flow
```

---

## Configuration: Enable/Disable Integration

Future configuration option:

```python
# .env or config
HEIMDALL_ENABLED=true              # Master enable
HEIMDALL_AUTO_RECORD_OUTCOMES=false # Still manual in V1
HEIMDALL_ENRICH_CASE_VIEW=false     # Disabled by default
HEIMDALL_RISK_ADJUSTMENT=false      # Disabled by default
```

**Default:** All disabled to ensure zero impact.

---

## Metrics for Successful Integration

When Phase 2 integration is attempted, measure:

1. **Availability:** Heimdall context available 95%+ of query time
2. **Latency:** Bridge calls < 500ms p95
3. **Accuracy:** Outcome predictions within 10% of actual (Month 3+)
4. **Adoption:** Team using hints/context 20%+ of cases by Month 2
5. **Quality:** Lessons prove actionable in 70%+ of applicable cases
6. **Reliability:** Zero execution failures due to Heimdall failures

---

## Migration: From Isolated to Integrated

### Week 1-2 (Post-Launch)
- Execution layer stable
- Heimdall intake optional
- No integration

### Week 3-4
- Opt-in outcome recording
- Team building knowledge base
- Still fully manual

### Month 2
- Heimdall context in UI (advisory)
- Risk scoring enhanced (with fallback)
- Team finds insights valuable

### Month 3
- Action enrichment active
- Task generation uses Heimdall
- Market memory actively built

### Q2+
- Full integration with command fallbacks
- Advanced learning algorithms
- Multi-zone decision support

---

## Rollback Plan

If integration causes issues:

1. **Immediate:** Remove Heimdall router from app.include_router()
2. **Rollback:** Execution layer unchanged, continues operating
3. **Assessment:** Identify Heimdall issue
4. **Fix:** Update Heimdall logic
5. **Redeploy:** Re-register router

**Time to rollback:** <5 minutes
**Data loss:** None
**Execution impact:** Zero

---

## Next Steps

### Phase 1 (Now)
✅ Heimdall runs independently  
✅ Integration docs written  
✅ Bridge functions designed (not implemented)  

### Phase 2+ (Month 1+)
⏳ Implement bridge.py functions  
⏳ Add outcome recording to execution  
⏳ Enable advisory context in execution UI  
⏳ Monitor metrics  
⏳ Iterate based on team feedback  

### Success Definition

Heimdall is "successfully integrated" when:
- Execution layer fully stable
- 90%+ of deals have recorded outcomes
- Team uses Heimdall context in 20%+ of decisions
- Predicted metrics within 15% of actual
- Zero execution failures from Heimdall

---

**Status:** Ready for Phase 1 deployment (isolated). Phase 2 integration planned for Month 1+.
