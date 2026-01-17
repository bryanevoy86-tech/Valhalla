"""
Batch 2 - Brain Intelligence + Deal Quality: Examples & Demonstrations
Shows how to use all 10 activation blocks with practical scenarios.
"""

import logging
from datetime import datetime, timedelta
from services.brain_intelligence import (
    SourceRegistry,
    SourceType,
    SourceQualityScorer,
    SourceLifecycleManager,
    MarketRegistry,
    DealCapCalculator,
    DuplicateResolver,
    StageEscalationEngine,
    ConePrioritizer,
    ShieldMonitor,
    DecisionLogger,
    BrainIntelligenceOrchestrator,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 11: Source Registry (Profiles per Lead Source)
# ============================================================================

def example_source_registry():
    """Example: Setting up source profiles."""
    print("\n" + "="*70)
    print("EXAMPLE 11: Source Registry - Lead Source Profiles")
    print("="*70)
    
    registry = SourceRegistry()
    
    # Add various lead sources
    print("\nAdding lead sources...\n")
    
    zillow = registry.add_source(
        "Zillow",
        SourceType.PUBLIC_LISTING,
        risk_score=0.3,
        conversion_rate=0.05,
        volume_monthly=500,
        cost_per_lead=2.50,
        metadata={'url': 'https://www.zillow.com'}
    )
    
    mls = registry.add_source(
        "Local MLS",
        SourceType.MLS,
        risk_score=0.2,
        conversion_rate=0.12,
        volume_monthly=100,
        cost_per_lead=0.0,
        metadata={'broker': 'Local Real Estate Association'}
    )
    
    referral = registry.add_source(
        "Referral Network",
        SourceType.REFERRAL,
        risk_score=0.1,
        conversion_rate=0.25,
        volume_monthly=50,
        cost_per_lead=5.00,
        metadata={'network': 'Trusted Agents'}
    )
    
    # Display sources
    print("Active Sources:")
    for source in registry.get_active_sources():
        print(f"  ✓ {source.source_name}")
        print(f"    Type: {source.source_type.value}")
        print(f"    Risk: {source.risk_score}, Conversion: {source.conversion_rate}")
        print(f"    Monthly Volume: {source.volume_monthly}")
        print()


# ============================================================================
# EXAMPLE 12: Source Quality Scoring
# ============================================================================

def example_source_quality_scoring():
    """Example: Scoring source quality."""
    print("\n" + "="*70)
    print("EXAMPLE 12: Source Quality Scoring")
    print("="*70)
    
    registry = SourceRegistry()
    scorer = SourceQualityScorer(registry)
    
    # Add sources
    registry.add_source("Premium MLS", SourceType.MLS, 0.15, 0.18, cost_per_lead=1.0)
    registry.add_source("Facebook Ads", SourceType.SOCIAL, 0.45, 0.08, cost_per_lead=8.0)
    registry.add_source("Direct Referral", SourceType.DIRECT, 0.05, 0.30, cost_per_lead=0.0)
    
    print("\nSource Quality Scores (0-1, higher is better):\n")
    
    for source_name, score in scorer.rank_sources():
        print(f"  {source_name:20} Score: {score:.3f}")
        
        # Add some performance history
        profile = registry.get_source(source_name)
        if profile:
            profile.update_performance(100, int(score * 100))
    
    print("\n✓ Ranking by quality score complete")


# ============================================================================
# EXAMPLE 13: Automatic Source Kill / Pause Logic
# ============================================================================

def example_source_lifecycle_management():
    """Example: Managing source lifecycle."""
    print("\n" + "="*70)
    print("EXAMPLE 13: Automatic Source Kill/Pause Logic")
    print("="*70)
    
    registry = SourceRegistry()
    scorer = SourceQualityScorer(registry)
    lifecycle = SourceLifecycleManager(registry, scorer)
    
    # Set custom thresholds
    lifecycle.set_thresholds(pause=0.25, kill=0.10)
    
    # Add sources with varying quality
    registry.add_source("High Quality", SourceType.MLS, 0.1, 0.20)
    registry.add_source("Medium Quality", SourceType.PORTAL, 0.4, 0.08)
    registry.add_source("Low Quality", SourceType.SOCIAL, 0.7, 0.02)
    
    print("\nEvaluating source health:\n")
    
    for source in registry.list_sources():
        result = lifecycle.evaluate_source_health(source.source_name)
        
        status_icon = "✓" if result['action'] == 'none' else "⚠" if result['action'] == 'pause' else "✗"
        print(f"  {status_icon} {result['source']}")
        print(f"    Score: {result['score']:.3f}")
        print(f"    Action: {result['action'].upper()}")
        print(f"    Reason: {result['reason']}")
        print()
    
    print(f"✓ Lifecycle evaluation complete ({len(lifecycle.action_log)} actions logged)")


# ============================================================================
# EXAMPLE 14: Market Zone Profiles
# ============================================================================

def example_market_zones():
    """Example: Market zone profiles."""
    print("\n" + "="*70)
    print("EXAMPLE 14: Market Zone Profiles (City/Region)")
    print("="*70)
    
    market = MarketRegistry()
    
    # Add market zones
    print("\nAdding market zones:\n")
    
    zones_data = [
        ("San Francisco", 1500000, 0.7),
        ("Detroit", 250000, 0.4),
        ("Austin", 600000, 0.5),
        ("New York", 800000, 0.6),
        ("Phoenix", 450000, 0.35),
    ]
    
    for zone_name, avg_price, risk_factor in zones_data:
        market.add_zone(zone_name, avg_price, risk_factor, 
                       inventory_level=0.6, demand_factor=0.7)
        print(f"  ✓ {zone_name:20} Avg: ${avg_price:>10,.0f}  Risk: {risk_factor}")


# ============================================================================
# EXAMPLE 15: Auto-Adjusted Caps per Zone
# ============================================================================

def example_auto_adjusted_caps():
    """Example: Auto-adjusted deal caps."""
    print("\n" + "="*70)
    print("EXAMPLE 15: Auto-Adjusted Caps per Zone")
    print("="*70)
    
    market = MarketRegistry()
    calculator = DealCapCalculator(market)
    
    # Setup zones
    market.add_zone("San Francisco", 1500000, 0.7)
    market.add_zone("Detroit", 250000, 0.4)
    market.add_zone("Austin", 600000, 0.5)
    
    print("\nDeal Caps by Zone:\n")
    
    caps = calculator.get_all_caps(method='basic')
    for zone, cap in caps.items():
        zone_obj = market.get_zone(zone)
        print(f"  {zone:20} Cap: ${cap:>10,.2f} (Avg: ${zone_obj.average_price:>10,.0f})")
    
    print("\nDemand-Adjusted Caps:\n")
    
    caps_adjusted = calculator.get_all_caps(method='demand_adjusted')
    for zone, cap in caps_adjusted.items():
        print(f"  {zone:20} Adjusted Cap: ${cap:>10,.2f}")


# ============================================================================
# EXAMPLE 16: Duplicate & Identity Resolution
# ============================================================================

def example_duplicate_resolution():
    """Example: Resolving duplicate leads."""
    print("\n" + "="*70)
    print("EXAMPLE 16: Duplicate & Identity Resolution")
    print("="*70)
    
    resolver = DuplicateResolver()
    
    # Sample lead data with duplicates
    leads = [
        {
            "id": "1",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-0001",
            "address": None
        },
        {
            "id": "2",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": None,
            "address": "123 Main St"
        },
        {
            "id": "3",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": None,
            "address": "456 Oak Ave"
        },
        {
            "id": "4",
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "phone": "555-0002",
            "address": None
        },
        {
            "id": "5",
            "name": "John D.",
            "email": "john@example.com",
            "phone": "555-0001",
            "address": None
        }
    ]
    
    print(f"\nInput: {len(leads)} leads (with duplicates)\n")
    for lead in leads:
        print(f"  - {lead['name']:20} {lead['email']}")
    
    # Resolve duplicates
    unique_leads = resolver.resolve_duplicates(leads, identity_field='email')
    
    print(f"\nOutput: {len(unique_leads)} unique leads\n")
    for lead in unique_leads:
        print(f"  ✓ {lead['name']:20} {lead['email']:25} {lead.get('address', 'N/A')}")
    
    print(f"\n✓ Resolved {len(leads) - len(unique_leads)} duplicates")


# ============================================================================
# EXAMPLE 17: Stuck-Stage Escalation Engine
# ============================================================================

def example_stuck_stage_escalation():
    """Example: Detecting and escalating stuck leads."""
    print("\n" + "="*70)
    print("EXAMPLE 17: Stuck-Stage Escalation Engine")
    print("="*70)
    
    escalator = StageEscalationEngine()
    
    # Sample leads at various stages
    leads = [
        {"id": "L1", "name": "John", "stage": "lead", "stage_duration_days": 3},
        {"id": "L2", "name": "Jane", "stage": "contact", "stage_duration_days": 8},
        {"id": "L3", "name": "Bob", "stage": "negotiation", "stage_duration_days": 20},
        {"id": "L4", "name": "Alice", "stage": "closing", "stage_duration_days": 2},
        {"id": "L5", "name": "Charlie", "stage": "contact", "stage_duration_days": 5},
    ]
    
    print("\nEvaluating lead progression:\n")
    
    escalated_count = 0
    for lead in leads:
        result = escalator.evaluate_lead_progression(lead)
        
        icon = "⚠ ESCALATE" if result['is_escalated'] else "✓ Normal"
        print(f"  {icon:15} {lead['name']:10} at {result['stage']:12} "
              f"({result['stage_duration_days']} days, threshold: {result['threshold_days']})")
        
        if result['is_escalated']:
            escalated_count += 1
            print(f"                  Priority: {result['priority'].upper()}")
    
    print(f"\n✓ {escalated_count} leads need escalation")


# ============================================================================
# EXAMPLE 18: Cone Prioritization Tuning (Top-10)
# ============================================================================

def example_cone_prioritization():
    """Example: Cone prioritization for top leads."""
    print("\n" + "="*70)
    print("EXAMPLE 18: Cone Prioritization Tuning (Top-10 / Big Game)")
    print("="*70)
    
    prioritizer = ConePrioritizer()
    
    # Sample leads with scoring factors
    leads = [
        {
            "id": "D1",
            "name": "Large Transaction",
            "deal_size_score": 0.95,
            "conversion_likelihood": 0.8,
            "timeline_score": 0.7,
            "relationship_strength": 0.6
        },
        {
            "id": "D2",
            "name": "Quick Close",
            "deal_size_score": 0.5,
            "conversion_likelihood": 0.9,
            "timeline_score": 0.95,
            "relationship_strength": 0.4
        },
        {
            "id": "D3",
            "name": "Established Relationship",
            "deal_size_score": 0.7,
            "conversion_likelihood": 0.85,
            "timeline_score": 0.6,
            "relationship_strength": 0.95
        },
        {
            "id": "D4",
            "name": "Risky Deal",
            "deal_size_score": 0.6,
            "conversion_likelihood": 0.3,
            "timeline_score": 0.4,
            "relationship_strength": 0.2
        },
        {
            "id": "D5",
            "name": "Medium Opportunity",
            "deal_size_score": 0.6,
            "conversion_likelihood": 0.7,
            "timeline_score": 0.5,
            "relationship_strength": 0.5
        },
    ]
    
    # Get top 3
    top_leads = prioritizer.prioritize_leads(leads, top_n=3)
    
    print("\nTop 3 Prioritized Leads (Big Game):\n")
    
    for i, lead in enumerate(top_leads, 1):
        print(f"  {i}. {lead['name']}")
        print(f"     Deal Size: {lead['deal_size_score']:.1%}")
        print(f"     Conversion: {lead['conversion_likelihood']:.1%}")
        print()


# ============================================================================
# EXAMPLE 19: Shield Telemetry Thresholds
# ============================================================================

def example_shield_monitoring():
    """Example: Shield monitoring and threshold alerts."""
    print("\n" + "="*70)
    print("EXAMPLE 19: Shield Telemetry Thresholds")
    print("="*70)
    
    shield = ShieldMonitor()
    
    # Register shields
    shield.register_shield("Risk Shield", warning_threshold=0.6, critical_threshold=0.8, unit="%")
    shield.register_shield("Compliance Shield", warning_threshold=0.4, critical_threshold=0.7, unit="%")
    shield.register_shield("Quality Shield", warning_threshold=0.3, critical_threshold=0.1, unit="")
    
    print("\nSimulating shield values:\n")
    
    test_values = {
        "Risk Shield": [0.45, 0.62, 0.85],
        "Compliance Shield": [0.35, 0.45, 0.75],
        "Quality Shield": [0.5, 0.35, 0.08],
    }
    
    for shield_name, values in test_values.items():
        print(f"  {shield_name}:")
        for value in values:
            alert_level = shield.update_shield_value(shield_name, value)
            icon = "✓" if alert_level.value == "safe" else "⚠" if alert_level.value == "warning" else "✗"
            print(f"    {icon} {alert_level.value.upper():10} (Value: {value})")


# ============================================================================
# EXAMPLE 20: Decision Reasoning Log
# ============================================================================

def example_decision_reasoning_log():
    """Example: Decision reasoning log."""
    print("\n" + "="*70)
    print("EXAMPLE 20: Decision Reasoning Log (Why This Happened)")
    print("="*70)
    
    decision_log = DecisionLogger()
    
    # Log various decisions
    print("\nLogging key decisions:\n")
    
    decisions = [
        {
            "type": "Lead Scoring",
            "category": DecisionLogger.DecisionCategory.LEAD_SCORING,
            "reason": "Lead converted from contact in 5 days, indicating high engagement",
            "confidence": 0.92,
        },
        {
            "type": "Source Pause",
            "category": DecisionLogger.DecisionCategory.SOURCE_MANAGEMENT,
            "reason": "Quality score dropped to 0.22 due to consistent low conversion rates",
            "confidence": 0.85,
        },
        {
            "type": "Lead Escalation",
            "category": DecisionLogger.DecisionCategory.ESCALATION,
            "reason": "Lead stuck in negotiation for 18 days, exceeds threshold of 14 days",
            "confidence": 1.0,
        },
        {
            "type": "Deal Approval",
            "category": DecisionLogger.DecisionCategory.DEAL_APPROVAL,
            "reason": "Deal size $1.2M in San Francisco exceeds zone cap of $450K, but relationship_strength 0.95",
            "confidence": 0.78,
        },
    ]
    
    for decision in decisions:
        decision_id = decision_log.log_decision(**decision)
        print(f"  ✓ {decision['type']}")
        print(f"    Confidence: {decision['confidence']:.0%}")
        print(f"    Reason: {decision['reason']}")
        print()
    
    print(f"✓ {len(decision_log.decisions)} decisions logged")


# ============================================================================
# INTEGRATED WORKFLOW EXAMPLE
# ============================================================================

def example_integrated_workflow():
    """Example: Complete workflow using all components."""
    print("\n" + "="*70)
    print("INTEGRATED WORKFLOW: Complete Deal Analysis Pipeline")
    print("="*70)
    
    # Initialize orchestrator
    brain = BrainIntelligenceOrchestrator()
    
    print("\n1. Setting up source intelligence...")
    
    brain.source_registry.add_source("Premium MLS", SourceType.MLS, 0.15, 0.20, cost_per_lead=1.0)
    brain.source_registry.add_source("Social Media", SourceType.SOCIAL, 0.55, 0.05, cost_per_lead=5.0)
    brain.source_registry.add_source("Referrals", SourceType.REFERRAL, 0.05, 0.35, cost_per_lead=0.0)
    
    print("   ✓ 3 sources registered")
    
    print("\n2. Setting up market zones...")
    
    brain.market_registry.add_zone("San Francisco", 1500000, 0.7)
    brain.market_registry.add_zone("Austin", 600000, 0.5)
    
    print("   ✓ 2 market zones configured")
    
    print("\n3. Analyzing deal from Premium MLS in Austin...")
    
    deal = {
        "id": "DEAL-001",
        "source": "Premium MLS",
        "zone": "Austin",
        "name": "Multi-family property",
        "deal_size_score": 0.85,
        "conversion_likelihood": 0.80,
        "timeline_score": 0.75,
        "relationship_strength": 0.70
    }
    
    analysis = brain.analyze_deal(deal)
    
    print(f"   Source Quality: {analysis['components']['source']['quality_score']:.3f}")
    print(f"   Zone Cap: ${analysis['components']['zone']['deal_cap']:,.2f}")
    print(f"   Priority: {analysis['components']['priority']['rank'].upper()}")
    
    print("\n4. Logging decision reasoning...")
    
    brain.decision_logger.log_decision(
        "Deal Approval",
        DecisionLogger.DecisionCategory.DEAL_APPROVAL,
        "High quality source, strong market conditions, excellent relationship",
        confidence=0.92
    )
    
    print("   ✓ Decision logged with reasoning")
    
    print("\n5. System Status:")
    status = brain.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")


# ============================================================================
# Run all examples
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("█ BATCH 2: BRAIN INTELLIGENCE + DEAL QUALITY EXAMPLES")
    print("█ 10 Activation Blocks (11-20) Implementation & Usage")
    print("█" * 70)
    
    try:
        example_source_registry()
        example_source_quality_scoring()
        example_source_lifecycle_management()
        example_market_zones()
        example_auto_adjusted_caps()
        example_duplicate_resolution()
        example_stuck_stage_escalation()
        example_cone_prioritization()
        example_shield_monitoring()
        example_decision_reasoning_log()
        example_integrated_workflow()
        
        print("\n" + "█" * 70)
        print("█ All examples completed successfully!")
        print("█" * 70 + "\n")
    
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
