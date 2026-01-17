# Batch 2 Implementation Guide

**Technical Deep Dive into Brain Intelligence + Deal Quality**

**Version:** 1.0.0  
**Date:** December 2024  
**Audience:** Developers, Architects

## Architecture Overview

### Design Principles

1. **Composition Over Inheritance**
   - Each component is independent
   - Orchestrator coordinates
   - Minimal coupling between blocks

2. **Registry Pattern**
   - SourceRegistry manages all sources
   - MarketRegistry manages all zones
   - Centralized configuration

3. **Strategy Pattern**
   - DealCapCalculator supports multiple methods
   - SourceLifecycleManager has configurable thresholds
   - Extensible scoring algorithms

4. **Observer Pattern**
   - ShieldMonitor notifies subscribers
   - DecisionLogger records all activities
   - Audit trail for compliance

### Data Models

#### SourceProfile (Block 11)

```python
class SourceProfile:
    source_name: str           # Unique identifier
    source_type: SourceType    # Enum: MLS, PORTAL, PUBLIC_LISTING, etc
    risk_score: float          # 0-1, higher = riskier
    cost_per_lead: float       # Dollar amount
    is_active: bool            # Active/Inactive status
    created_at: datetime       # Timestamp
    last_updated: datetime     # Timestamp
    conversion_rate: float     # 0-1 success rate
    consistency_score: float   # 0-1 lead quality consistency
```

#### MarketZone (Block 14)

```python
class MarketZone:
    zone_name: str             # City or region name
    average_price: float       # Median property price
    zone_risk_factor: float    # 0-1, market risk
    demand_factor: float       # 0-2, demand multiplier
    inventory_factor: float    # 0-2, inventory multiplier
    created_at: datetime       # Timestamp
```

#### Decision (Block 20)

```python
class Decision:
    decision_id: str           # UUID
    decision_type: str         # Category name
    category: DecisionCategory # Enum
    reasoning: str             # Explanation text
    confidence: float          # 0-1 confidence score
    timestamp: datetime        # When decided
    context_data: dict         # Additional metadata
```

## Implementation Details

### Block 11: Source Registry

**Purpose:** Maintain centralized source profiles

```python
registry = SourceRegistry()

# Add new source
source = registry.add_source(
    source_name="MLS Database",
    source_type=SourceType.MLS,
    risk_score=0.25,
    cost_per_lead=0.15
)

# Update existing
registry.update_source("MLS Database", risk_score=0.20)

# Query
all_sources = registry.list_sources()
active = registry.get_active_sources()
specific = registry.get_source("MLS Database")
```

**Key Methods:**
- `add_source()`: Create new source profile
- `get_source()`: Retrieve by name
- `update_source()`: Modify attributes
- `list_sources()`: Get all sources
- `get_active_sources()`: Filter active only
- `deactivate_source()`: Mark inactive

### Block 12: Source Quality Scoring

**Purpose:** Evaluate source quality on 0-1 scale

```python
scorer = SourceQualityScorer(registry)

# Calculate quality for one source
score = scorer.calculate_quality_score("MLS Database")
# Returns: 0.75 (75% quality)

# Rank all sources
ranked = scorer.rank_sources()
# Returns: [("Source1", 0.85), ("Source2", 0.62), ...]
```

**Scoring Formula:**

```
Quality Score = 
    0.40 * (conversion_rate) +
    0.30 * (1 - risk_score) +
    0.20 * (consistency_score) +
    0.10 * (1 - normalized_cost)
```

Where normalized_cost is cost relative to max cost across all sources.

**Key Methods:**
- `calculate_quality_score(source_name)`: Get score 0-1
- `rank_sources()`: Sort by quality descending
- `get_score_components(source_name)`: Debug individual components

### Block 13: Source Lifecycle Management

**Purpose:** Auto-escalate poor-performing sources

```python
lifecycle = SourceLifecycleManager(registry, scorer)

# Set decision thresholds (configurable)
lifecycle.set_thresholds(pause=0.4, kill=0.2)

# Evaluate a source
result = lifecycle.evaluate_source_health("MLS Database")
# Returns:
# {
#     'is_escalated': False,
#     'action': 'NONE',
#     'reason': 'Quality score 0.75 is healthy',
#     'quality_score': 0.75
# }

# For poor source:
result = lifecycle.evaluate_source_health("Bad Source")
# Returns:
# {
#     'is_escalated': True,
#     'action': 'PAUSE',
#     'reason': 'Quality score 0.35 below pause threshold 0.4',
#     'quality_score': 0.35
# }
```

**Actions:**
- `NONE`: Quality healthy, no action
- `PAUSE`: Quality at risk, pause new leads
- `KILL`: Quality critical, stop accepting leads

**Key Methods:**
- `set_thresholds(pause, kill)`: Configure limits
- `evaluate_source_health(source_name)`: Check status
- `apply_action(source_name, action)`: Execute pause/kill
- `get_health_report()`: Summary of all sources

### Block 14: Market Zones

**Purpose:** Define geographic market segments

```python
market = MarketRegistry()

# Add market zone
zone = market.add_zone(
    zone_name="Austin, TX",
    average_price=600000,
    zone_risk_factor=0.5,
    demand_factor=0.8,
    inventory_factor=1.2
)

# Query
all_zones = market.list_zones()
specific = market.get_zone("Austin, TX")

# Update
market.update_zone("Austin, TX", zone_risk_factor=0.45)
```

**Zone Factors:**
- `average_price`: Baseline for cap calculations
- `zone_risk_factor`: 0 (safe) to 1 (risky)
- `demand_factor`: 0.5 (low demand) to 2.0 (high demand)
- `inventory_factor`: 0.5 (scarce) to 2.0 (abundant)

**Key Methods:**
- `add_zone()`: Create market definition
- `get_zone()`: Retrieve by name
- `update_zone()`: Modify attributes
- `list_zones()`: Get all zones

### Block 15: Auto-Adjusted Deal Caps

**Purpose:** Calculate maximum deal caps by zone

```python
calculator = DealCapCalculator(market)

# Method 1: Basic cap
basic = calculator.calculate_deal_cap("Austin, TX", method='basic')
# Formula: price * (1 - risk_factor)
# Example: 600000 * (1 - 0.5) = 300000

# Method 2: Demand-adjusted
demand = calculator.calculate_deal_cap("Austin, TX", method='demand_adjusted')
# Formula: basic_cap * demand_factor
# Example: 300000 * 0.8 = 240000

# Method 3: Inventory-adjusted
inventory = calculator.calculate_deal_cap("Austin, TX", method='inventory_adjusted')
# Formula: basic_cap * inventory_factor
# Example: 300000 * 1.2 = 360000
```

**Calculation Methods:**

| Method | Formula | Use Case |
|--------|---------|----------|
| basic | price × (1 - risk) | Baseline |
| demand_adjusted | basic × demand_factor | High/low demand zones |
| inventory_adjusted | basic × inventory_factor | Scarce/abundant inventory |

**Key Methods:**
- `calculate_deal_cap(zone, method)`: Get cap amount
- `compare_methods(zone)`: Show all methods side-by-side
- `set_default_method(method)`: Configure default

### Block 16: Duplicate Resolution

**Purpose:** Identify and merge duplicate leads

```python
resolver = DuplicateResolver()

leads = [
    {"email": "john@example.com", "phone": "555-1234", "name": "John"},
    {"email": "john@example.com", "phone": None, "name": "John Doe"},
    {"email": "jane@example.com", "phone": "555-5678", "name": "Jane"},
]

# Resolve duplicates
unique = resolver.resolve_duplicates(leads)
# Returns 2 leads (John merged, Jane separate)

unique[0]
# {
#     "email": "john@example.com",
#     "phone": "555-1234",  # Filled from first lead
#     "name": "John Doe",   # Uses more complete name
#     "merged_from": 2
# }
```

**Matching Logic:**
1. First pass: Match by email
2. Second pass: Match by phone (if configured)
3. Merge: Non-null fields from sources, prefer complete data

**Key Methods:**
- `resolve_duplicates(leads)`: Process all leads
- `find_duplicates(leads)`: Return groups without merging
- `merge_leads(lead1, lead2)`: Combine two leads
- `set_matching_fields()`: Configure match criteria

### Block 17: Stuck-Stage Escalation

**Purpose:** Detect leads stalled in stages too long

```python
escalator = StageEscalationEngine()

# Default thresholds (days)
# Lead: 7, Negotiation: 14, Documentation: 7, Other: 30

# Evaluate a lead
lead = {
    "name": "John",
    "stage": "negotiation",
    "stage_duration_days": 20
}

result = escalator.evaluate_lead_progression(lead)
# Returns:
# {
#     'is_escalated': True,
#     'priority': 'critical',
#     'days_over': 6,
#     'reason': 'Lead in negotiation 20 days (threshold: 14)'
# }

# Set custom threshold
escalator.set_threshold('negotiation', threshold_days=21)

# Now it won't escalate
result = escalator.evaluate_lead_progression(lead)
# is_escalated: False
```

**Priority Calculation:**

```
if days_over == 0:           priority = 'low'
elif days_over <= 5:         priority = 'medium'
elif days_over <= 10:        priority = 'high'
else:                        priority = 'critical'
```

**Key Methods:**
- `evaluate_lead_progression(lead)`: Check escalation status
- `set_threshold(stage, days)`: Configure per-stage
- `get_escalated_leads(leads)`: Filter all escalated
- `get_escalation_report()`: Summary report

### Block 18: Cone Prioritization

**Purpose:** Rank leads by prioritization factors

```python
prioritizer = ConePrioritizer()

leads = [
    {
        "name": "Lead A",
        "deal_size_score": 0.9,          # Big deal
        "conversion_likelihood": 0.7,    # Likely to convert
        "timeline_score": 0.6,           # Mid timeline
        "relationship_strength": 0.5     # Moderate relationship
    },
    {
        "name": "Lead B",
        "deal_size_score": 0.5,
        "conversion_likelihood": 0.9,    # Very likely to convert
        "timeline_score": 0.9,           # Short timeline
        "relationship_strength": 0.8     # Strong relationship
    }
]

# Get top 1
top = prioritizer.prioritize_leads(leads, top_n=1)
# Returns [Lead B] (better overall score)

# Calculate scores
scores = prioritizer.calculate_scores(leads)
# [
#     ("Lead A", 0.755),  # 0.9*0.35 + 0.7*0.35 + 0.6*0.2 + 0.5*0.1
#     ("Lead B", 0.815)   # 0.5*0.35 + 0.9*0.35 + 0.9*0.2 + 0.8*0.1
# ]
```

**Weighting:**
- Deal Size: 35% (big deals prioritized)
- Conversion: 35% (likely closes prioritized)
- Timeline: 20% (short timelines prioritized)
- Relationship: 10% (strong relationships prioritized)

**Key Methods:**
- `prioritize_leads(leads, top_n)`: Get ranked top N
- `calculate_scores(leads)`: Get all scores with rankings
- `set_weights()`: Customize weighting
- `get_top_game_leads()`: Filter "big game" leads

### Block 19: Shield Telemetry Monitoring

**Purpose:** Monitor KPIs with multi-level alerts

```python
shield = ShieldMonitor()

# Register a monitored metric
shield.register_shield(
    shield_name="Portfolio Risk",
    warning_threshold=0.60,
    critical_threshold=0.80
)

# Update value and get alert
alert = shield.update_shield_value("Portfolio Risk", 0.55)
# Returns: ShieldAlert.SAFE

alert = shield.update_shield_value("Portfolio Risk", 0.65)
# Returns: ShieldAlert.WARNING

alert = shield.update_shield_value("Portfolio Risk", 0.85)
# Returns: ShieldAlert.CRITICAL

# Subscribe to alerts
def on_alert(shield_name, alert_level, value):
    print(f"{shield_name}: {alert_level} at {value:.1%}")

shield.subscribe(on_alert)
```

**Alert Levels:**

```
SAFE     (✅): value < warning_threshold
WARNING  (⚠️): warning_threshold ≤ value < critical_threshold
CRITICAL (🔴): value ≥ critical_threshold
```

**Key Methods:**
- `register_shield(name, warning, critical)`: Define metric
- `update_shield_value(name, value)`: Update & check
- `subscribe(callback)`: Subscribe to alerts
- `get_status()`: Current status of all shields
- `get_history()`: Historical values

### Block 20: Decision Reasoning Log

**Purpose:** Comprehensive audit trail for compliance

```python
logger = DecisionLogger()

# Log a decision
decision_id = logger.log_decision(
    type="Lead Approval",
    category=DecisionLogger.DecisionCategory.LEAD_SCORING,
    reasoning="High conversion rate, established relationship",
    confidence=0.92
)
# Returns: "dec_abc123def456"

# Retrieve decision
decision = logger.get_decision(decision_id)
# {
#     'decision_id': 'dec_abc123def456',
#     'type': 'Lead Approval',
#     'category': 'LEAD_SCORING',
#     'reasoning': 'High conversion rate, established relationship',
#     'confidence': 0.92,
#     'timestamp': datetime(2024, 12, 1, 15, 30, 0),
#     'context': {}
# }

# Query decisions
decisions = logger.get_decisions_by_type("Lead Approval")
decisions = logger.get_decisions_by_category(DecisionCategory.LEAD_SCORING)
decisions = logger.get_decisions_by_date_range(start_date, end_date)

# Export for audit
json_export = logger.export_decisions(format='json')
csv_export = logger.export_decisions(format='csv')
```

**Decision Categories:**

```python
class DecisionCategory(Enum):
    LEAD_SCORING = "lead_scoring"
    DEAL_APPROVAL = "deal_approval"
    SOURCE_MANAGEMENT = "source_management"
    RISK_ALERT = "risk_alert"
    OTHER = "other"
```

**Key Methods:**
- `log_decision()`: Record a decision
- `get_decision(id)`: Retrieve by ID
- `get_decisions_by_type()`: Filter by type
- `get_decisions_by_category()`: Filter by category
- `get_decisions_by_date_range()`: Filter by date
- `export_decisions()`: Export to JSON/CSV
- `search_decisions()`: Full-text search

## Common Implementation Patterns

### Pattern 1: Quality-Based Sourcing

```python
# Step 1: Score all sources
ranked = brain.quality_scorer.rank_sources()

# Step 2: For top sources, accept leads
# For poor sources, check escalation
for source_name, score in ranked:
    health = brain.lifecycle_manager.evaluate_source_health(source_name)
    
    if not health['is_escalated']:
        print(f"✅ Accept from {source_name}")
    else:
        print(f"⚠️ Review {source_name}: {health['reason']}")
        
    brain.decision_logger.log_decision(
        f"Source {source_name} Status",
        DecisionLogger.DecisionCategory.SOURCE_MANAGEMENT,
        f"Score: {score:.1%}, Action: {health['action']}"
    )
```

### Pattern 2: Geographic Cap Management

```python
# Step 1: Get all zones
zones = brain.market_registry.list_zones()

# Step 2: Calculate caps per zone
caps_by_zone = {}
for zone in zones:
    cap = brain.calculator.calculate_deal_cap(
        zone.zone_name,
        method='demand_adjusted'
    )
    caps_by_zone[zone.zone_name] = cap

# Step 3: Log decision
brain.decision_logger.log_decision(
    "Zone Caps Updated",
    DecisionLogger.DecisionCategory.DEAL_APPROVAL,
    f"Calculated caps for {len(caps_by_zone)} zones"
)

return caps_by_zone
```

### Pattern 3: Lead Processing Pipeline

```python
# Step 1: Ingest leads from multiple sources
all_leads = fetch_from_sources()

# Step 2: Deduplicate
unique_leads = brain.duplicate_resolver.resolve_duplicates(all_leads)

# Step 3: Check for stuck stages
escalated = []
for lead in unique_leads:
    result = brain.escalator.evaluate_lead_progression(lead)
    if result['is_escalated']:
        escalated.append((lead, result))

# Step 4: Prioritize remaining leads
remaining = [l for l in unique_leads if l not in [e[0] for e in escalated]]
top_leads = brain.cone_prioritizer.prioritize_leads(remaining, top_n=10)

# Step 5: Log decisions
brain.decision_logger.log_decision(
    "Lead Processing Complete",
    DecisionLogger.DecisionCategory.LEAD_SCORING,
    f"Processed {len(all_leads)} leads → {len(unique_leads)} unique → {len(top_leads)} prioritized"
)

return top_leads, escalated
```

## Error Handling

### Common Exceptions

```python
# Handle missing source
try:
    score = brain.quality_scorer.calculate_quality_score("NonExistent")
except KeyError:
    print("Source not found")

# Handle invalid zone
try:
    cap = brain.calculator.calculate_deal_cap("Invalid Zone")
except ValueError:
    print("Zone not found")

# Handle bad lead data
try:
    resolved = brain.duplicate_resolver.resolve_duplicates(bad_leads)
except (KeyError, TypeError):
    print("Lead data incomplete")
```

### Recommended Approach

```python
def process_safely(lead):
    try:
        result = brain.escalator.evaluate_lead_progression(lead)
        return result
    except Exception as e:
        brain.decision_logger.log_decision(
            "Error Processing Lead",
            DecisionLogger.DecisionCategory.OTHER,
            f"Error: {str(e)}"
        )
        return None
```

## Performance Optimization

### For Large Lead Sets

```python
# Process in batches instead of all at once
batch_size = 1000
for i in range(0, len(leads), batch_size):
    batch = leads[i:i+batch_size]
    
    # Process batch
    unique = brain.duplicate_resolver.resolve_duplicates(batch)
    ranked = brain.cone_prioritizer.prioritize_leads(unique, top_n=10)
    
    # Log progress
    brain.decision_logger.log_decision(
        "Batch Processing",
        DecisionLogger.DecisionCategory.OTHER,
        f"Processed batch {i//batch_size + 1}"
    )
```

### Caching Recommendations

```python
# Cache ranked sources (refresh hourly)
import functools
import time

@functools.lru_cache(maxsize=1)
def get_ranked_sources_cached():
    return brain.quality_scorer.rank_sources()

# Invalidate cache after 1 hour
# In practice, use Redis or similar
```

## Testing Your Implementation

```python
# Test individual component
def test_source_registry():
    brain = BrainIntelligenceOrchestrator()
    assert brain.source_registry is not None
    brain.source_registry.add_source("Test", SourceType.MLS, 0.2, 0.1)
    assert brain.source_registry.get_source("Test") is not None

# Test workflow
def test_complete_workflow():
    brain = BrainIntelligenceOrchestrator()
    
    # Add source
    brain.source_registry.add_source("MLS", SourceType.MLS, 0.2, 0.15)
    
    # Add zone
    brain.market_registry.add_zone("Austin", 600000, 0.5)
    
    # Score
    score = brain.quality_scorer.calculate_quality_score("MLS")
    assert 0 < score < 1
    
    # Get cap
    cap = brain.calculator.calculate_deal_cap("Austin")
    assert cap > 0
```

## Extending the System

### Add Custom Scoring Method

```python
class CustomScorer:
    def score(self, source):
        # Your custom logic
        return 0.75

# Integrate into orchestrator
brain.custom_scorer = CustomScorer()
```

### Add New Decision Category

```python
class DecisionCategory(Enum):
    # ... existing ...
    CUSTOM_ALERT = "custom_alert"

# Use in logging
brain.decision_logger.log_decision(
    "Custom Decision",
    DecisionCategory.CUSTOM_ALERT,
    "Custom reasoning"
)
```

## References

- [BATCH_2_README.md](BATCH_2_README.md) - Quick start guide
- [BATCH_2_SUMMARY.md](BATCH_2_SUMMARY.md) - Overview & metrics
- [services/brain_intelligence_examples.py](services/brain_intelligence_examples.py) - Working code samples
- [tests/test_batch_2_brain_intelligence.py](tests/test_batch_2_brain_intelligence.py) - Test examples
