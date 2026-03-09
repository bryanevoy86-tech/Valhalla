# Batch 2: Brain Intelligence + Deal Quality

**Status:** ✅ Complete & Ready for Deployment

**Version:** 1.0.0  
**Date:** December 2024  
**Activation Blocks:** 11-20 (10 components)

## Quick Reference

| Block | Component | Purpose | Status |
|-------|-----------|---------|--------|
| 11 | Source Registry | Lead source profiles & tracking | ✅ Complete |
| 12 | Source Quality Scoring | Multi-metric source quality rating | ✅ Complete |
| 13 | Source Kill/Pause Logic | Auto-escalation for poor sources | ✅ Complete |
| 14 | Market Zones | Geographic market profiles | ✅ Complete |
| 15 | Auto-Adjusted Caps | Dynamic deal caps per zone | ✅ Complete |
| 16 | Duplicate Resolution | Email/ID-based lead deduplication | ✅ Complete |
| 17 | Stuck-Stage Escalation | Detect long-duration stages | ✅ Complete |
| 18 | Cone Prioritization | Top-10/big-game lead ranking | ✅ Complete |
| 19 | Shield Telemetry | Multi-level alert thresholds | ✅ Complete |
| 20 | Decision Logging | Comprehensive decision audit trail | ✅ Complete |

## Core Files

- **services/brain_intelligence.py** (3,000+ lines)
  - 11 core classes + 1 orchestrator
  - All 10 activation blocks implemented
  - Full type hints and docstrings
  
- **services/brain_intelligence_examples.py** (600+ lines)
  - 10 component examples (1 per block)
  - 1 integrated workflow example
  - All examples runnable and demonstrated

- **tests/test_batch_2_brain_intelligence.py** (500+ lines)
  - 11 test classes (1 per core component)
  - 50+ unit tests
  - Integration tests included

## Getting Started

### 1. Import the Orchestrator

```python
from services.brain_intelligence import BrainIntelligenceOrchestrator

brain = BrainIntelligenceOrchestrator()
```

### 2. Set Up Sources (Block 11)

```python
from services.brain_intelligence import SourceType

brain.source_registry.add_source(
    source_name="Zillow",
    source_type=SourceType.PUBLIC_LISTING,
    risk_score=0.3,
    cost_per_lead=0.05
)
```

### 3. Add Market Zones (Block 14)

```python
brain.market_registry.add_zone(
    zone_name="Austin",
    average_price=600000,
    zone_risk_factor=0.5,
    demand_factor=0.8,
    inventory_factor=1.2
)
```

### 4. Score & Rank Sources (Block 12)

```python
ranked = brain.quality_scorer.rank_sources()
for source_name, score in ranked:
    print(f"{source_name}: {score:.2%}")
```

### 5. Resolve Duplicates (Block 16)

```python
leads = [{"email": "john@test.com", ...}, ...]
unique_leads = brain.duplicate_resolver.resolve_duplicates(leads)
```

### 6. Prioritize Leads (Block 18)

```python
top_leads = brain.cone_prioritizer.prioritize_leads(leads, top_n=10)
```

## Key Concepts

### Quality Scoring (Block 12)
Weighted scoring formula:
- Conversion Rate: 40%
- Risk Score: 30%
- Consistency: 20%
- Cost per Lead: 10%

Result: 0-1 scale (higher = better)

### Deal Caps (Block 15)
Three calculation methods:
1. **Basic:** `price * (1 - risk_factor)`
2. **Demand-Adjusted:** `basic_cap * demand_factor`
3. **Inventory-Adjusted:** `basic_cap * inventory_factor`

### Source Lifecycle (Block 13)
- **Healthy:** Quality score > pause threshold
- **Pause:** Quality score between pause & kill thresholds
- **Kill:** Quality score < kill threshold

Default thresholds: Pause=0.4, Kill=0.2

### Stage Escalation (Block 17)
Default thresholds (days):
- Lead: 7 days
- Negotiation: 14 days
- Documentation: 7 days
- Other: 30 days

Configurable via `set_threshold()`.

### Shield Monitoring (Block 19)
Three alert levels:
1. **Safe:** Value < warning threshold
2. **Warning:** Value >= warning, < critical
3. **Critical:** Value >= critical threshold

### Decision Logging (Block 20)
Captures:
- Decision type & category
- Reasoning text
- Confidence score (optional)
- Timestamp
- Context data

Searchable by: ID, type, date range, category

## Running Examples

All examples from `brain_intelligence_examples.py` are runnable:

```python
from services.brain_intelligence_examples import (
    example_source_registry,
    example_source_quality_scoring,
    example_market_zones,
    example_auto_adjusted_caps,
    example_duplicate_resolution,
    example_stuck_stage_escalation,
    example_cone_prioritization,
    example_shield_monitoring,
    example_decision_reasoning_log,
    example_integrated_workflow
)

# Run any example
example_source_registry()
example_integrated_workflow()
```

## Testing

Run all Batch 2 tests:

```bash
python -m pytest tests/test_batch_2_brain_intelligence.py -v
```

Run specific test class:

```bash
python -m pytest tests/test_batch_2_brain_intelligence.py::TestSourceRegistry -v
```

Run with coverage:

```bash
python -m pytest tests/test_batch_2_brain_intelligence.py --cov=services.brain_intelligence
```

## Architecture

### Components Hierarchy

```
BrainIntelligenceOrchestrator (Main)
├── SourceRegistry (Block 11)
├── SourceQualityScorer (Block 12)
├── SourceLifecycleManager (Block 13)
├── MarketRegistry (Block 14)
├── DealCapCalculator (Block 15)
├── DuplicateResolver (Block 16)
├── StageEscalationEngine (Block 17)
├── ConePrioritizer (Block 18)
├── ShieldMonitor (Block 19)
└── DecisionLogger (Block 20)
```

### Data Flow

```
1. Add Sources → Source Registry
2. Score Sources → Quality Scorer
3. Monitor Source Health → Lifecycle Manager
4. Define Market Zones → Market Registry
5. Calculate Caps → Deal Cap Calculator
6. Process Leads → Duplicate Resolver
7. Detect Escalations → Stage Escalation Engine
8. Rank & Prioritize → Cone Prioritizer
9. Monitor Thresholds → Shield Monitor
10. Log All Decisions → Decision Logger
```

## Configuration

### Source Registry

```python
brain.source_registry.add_source(
    source_name="MLS",
    source_type=SourceType.MLS,
    risk_score=0.2,       # 0-1, higher = riskier
    cost_per_lead=0.15
)
```

### Market Registry

```python
brain.market_registry.add_zone(
    zone_name="San Francisco",
    average_price=1500000,
    zone_risk_factor=0.7,    # 0-1
    demand_factor=0.8,        # adjusts caps down
    inventory_factor=1.2      # adjusts caps up
)
```

### Lifecycle Manager

```python
brain.lifecycle_manager.set_thresholds(
    pause=0.4,    # Below this = pause source
    kill=0.2      # Below this = kill source
)
```

### Stage Escalation

```python
brain.escalator.set_threshold(
    stage_name='negotiation',
    threshold_days=14
)
```

## Common Patterns

### Pattern 1: Quality Audit

```python
# Rank all sources by quality
ranked = brain.quality_scorer.rank_sources()

for source_name, quality_score in ranked:
    source = brain.source_registry.get_source(source_name)
    print(f"{source_name}: {quality_score:.1%}")
    
    # Evaluate health
    health = brain.lifecycle_manager.evaluate_source_health(source_name)
    if health['is_escalated']:
        print(f"  ⚠️ Action Required: {health['reason']}")
```

### Pattern 2: Lead Processing Pipeline

```python
# Raw leads from multiple sources
raw_leads = fetch_from_sources()

# Step 1: Resolve duplicates
unique_leads = brain.duplicate_resolver.resolve_duplicates(raw_leads)

# Step 2: Escalate stuck stages
escalated = []
for lead in unique_leads:
    result = brain.escalator.evaluate_lead_progression(lead)
    if result['is_escalated']:
        escalated.append(lead)

# Step 3: Prioritize top leads
top_leads = brain.cone_prioritizer.prioritize_leads(unique_leads, top_n=10)

# Step 4: Log decisions
for lead in top_leads:
    brain.decision_logger.log_decision(
        "Lead Processing",
        DecisionLogger.DecisionCategory.LEAD_SCORING,
        f"Ranked {lead['name']} - Priority: {lead['priority']}"
    )
```

### Pattern 3: Zone Performance Analysis

```python
# Analyze all zones
zones = brain.market_registry.list_zones()

for zone in zones:
    basic_cap = brain.calculator.calculate_deal_cap(zone.zone_name, method='basic')
    demand_cap = brain.calculator.calculate_deal_cap(zone.zone_name, method='demand_adjusted')
    
    print(f"{zone.zone_name}:")
    print(f"  Base Cap: ${basic_cap:,.0f}")
    print(f"  Demand-Adjusted Cap: ${demand_cap:,.0f}")
    print(f"  Risk Factor: {zone.zone_risk_factor:.1%}")
```

### Pattern 4: Alert Management

```python
# Register telemetry shields
brain.shield_monitor.register_shield(
    shield_name="Portfolio Risk",
    warning_threshold=0.60,
    critical_threshold=0.80
)

# Update values (from external monitoring)
alert_level = brain.shield_monitor.update_shield_value(
    "Portfolio Risk",
    current_value=0.75
)

if alert_level == ShieldMonitor.ShieldAlert.CRITICAL:
    brain.decision_logger.log_decision(
        "Alert Triggered",
        DecisionLogger.DecisionCategory.RISK_ALERT,
        "Portfolio risk reached critical level",
        confidence=0.95
    )
```

## Integration with Batch 1

Batch 2 complements Batch 1 (Sandbox + Stability):

- **Batch 1** provides: Safety, isolation, error handling
- **Batch 2** provides: Intelligence, quality scoring, decision logic

Together they enable:
- Safe testing of new sources (via Batch 1 sandbox)
- Quality evaluation (via Batch 2 scoring)
- Automated escalations (via Batch 2 lifecycle + Batch 1 alerts)

## Monitoring & Operations

### Component Health Check

```python
status = brain.get_status()
print(f"Sources: {status['sources_count']}")
print(f"Active Sources: {status['active_sources_count']}")
print(f"Market Zones: {status['zones_count']}")
print(f"Decisions Logged: {status['total_decisions']}")
```

### Export Audit Trail

```python
# Export all decisions for compliance
decisions = brain.decision_logger.export_decisions(format='json')

# Save to file
with open('audit_trail.json', 'w') as f:
    f.write(decisions)
```

### Source Performance Report

```python
ranked = brain.quality_scorer.rank_sources()
report = []

for source_name, score in ranked:
    source = brain.source_registry.get_source(source_name)
    report.append({
        'source': source_name,
        'quality_score': score,
        'risk_score': source.risk_score,
        'cost_per_lead': source.cost_per_lead,
        'active': source.is_active
    })

import json
print(json.dumps(report, indent=2))
```

## Troubleshooting

**Q: Quality score is None**
A: Source doesn't exist. Use `brain.source_registry.list_sources()` to verify.

**Q: Deal cap is None**
A: Zone doesn't exist. Use `brain.market_registry.list_zones()` to verify.

**Q: Shield alert not triggering**
A: Check threshold configuration. Verify `update_shield_value()` is being called with actual metrics.

**Q: Duplicate resolution not merging**
A: Leads must have matching email OR matching ID. Verify email/ID fields exist.

## Performance Notes

- Source quality scoring: O(n) where n = number of sources
- Duplicate resolution: O(n²) for email matching, optimize if needed
- Lead prioritization: O(n log n) for sorting
- Stage escalation: O(n) evaluation per lead

For >100k leads, consider batch processing.

## Next Steps

1. Review [BATCH_2_SUMMARY.md](BATCH_2_SUMMARY.md) for detailed metrics
2. See [BATCH_2_DEPLOYMENT_CHECKLIST.md](BATCH_2_DEPLOYMENT_CHECKLIST.md) for deployment
3. Check [BATCH_2_INDEX.md](BATCH_2_INDEX.md) for complete navigation
4. Review examples in [services/brain_intelligence_examples.py](services/brain_intelligence_examples.py)

## Support & Questions

For implementation questions, review:
- The examples in `services/brain_intelligence_examples.py`
- Test cases in `tests/test_batch_2_brain_intelligence.py`
- Inline documentation in `services/brain_intelligence.py`

All code follows PEP 8 and includes comprehensive type hints.
