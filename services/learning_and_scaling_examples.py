"""
Batch 3: Learning + Scaling Safety - Working Examples
11 complete, runnable examples demonstrating all activation blocks 21-30
"""

from services.learning_and_scaling import (
    ABTracker, ScriptPromoter, DealPacketBuilder, LearningIngestor,
    OutcomeEvaluator, SafeModelUpdater, CloneReadinessScorer, CloneGateEnforcer,
    CloneAuditTrail, BrainVerificationSuite, LearningAndScalingOrchestrator
)


def example_ab_tracking():
    """Example: Block 21 - Script/Channel A/B Tracking."""
    print("\n" + "="*70)
    print("BLOCK 21: Script/Channel A/B Tracking")
    print("="*70)
    
    tracker = ABTracker()
    
    # Register script variants
    script_a = tracker.register_variant("Script A - High Energy", "script")
    script_b = tracker.register_variant("Script B - Low Pressure", "script")
    
    # Register channel variants
    email = tracker.register_variant("Email Channel", "channel")
    sms = tracker.register_variant("SMS Channel", "channel")
    
    print("\n📊 Registered A/B Test Variants:")
    print(f"  Script A: {script_a}")
    print(f"  Script B: {script_b}")
    print(f"  Email Channel: {email}")
    print(f"  SMS Channel: {sms}")
    
    # Track performance
    tracker.track_performance(script_a, 0.82, conversions=45, cost=2250)
    tracker.track_performance(script_b, 0.78, conversions=39, cost=1950)
    tracker.track_performance(email, 0.75, conversions=60, cost=600)
    tracker.track_performance(sms, 0.88, conversions=70, cost=700)
    
    print("\n📈 Performance Tracking:")
    print(f"  Script A: 82% (45 conversions, $2,250 total)")
    print(f"  Script B: 78% (39 conversions, $1,950 total)")
    print(f"  Email Channel: 75% (60 conversions, $600 total)")
    print(f"  SMS Channel: 88% (70 conversions, $700 total)")
    
    # Find winning variants
    best_script = tracker.get_winning_variant("script")
    best_channel = tracker.get_winning_variant("channel")
    
    print("\n🏆 Winning Variants:")
    print(f"  Best Script: {best_script['variant_name']} ({best_script['performance']:.1%})")
    print(f"  Best Channel: {best_channel['variant_name']} ({best_channel['performance']:.1%})")
    
    # Compare variants
    comparison = tracker.compare_variants([script_a, script_b, email, sms])
    print("\n📊 All Variants Ranked:")
    for i, variant in enumerate(comparison, 1):
        print(f"  {i}. {variant['variant_name']}: {variant['performance']:.1%} "
              f"(CPL: ${variant['cost_per_action']:.2f})")


def example_script_promotion():
    """Example: Block 22 - Performance-Based Script Promotion/Demotion."""
    print("\n" + "="*70)
    print("BLOCK 22: Performance-Based Script Promotion/Demotion")
    print("="*70)
    
    promoter = ScriptPromoter()
    
    # Register script versions
    script_v1 = promoter.register_script("High-Urgency Closer", "1.0")
    script_v2 = promoter.register_script("High-Urgency Closer", "2.0")
    
    print("\n📝 Registered Scripts:")
    print(f"  v1.0 ID: {script_v1}")
    print(f"  v2.0 ID: {script_v2}")
    
    # Evaluate scripts (triggers promotions)
    print("\n📊 Evaluation Round 1 (Experimental → Testing):")
    result1 = promoter.evaluate_script(script_v1, 0.87)
    print(f"  v1.0: {result1['old_status']} → {result1['new_status']} (Score: {result1['performance_score']:.1%})")
    
    print("\n📊 Evaluation Round 2 (Testing → Primary):")
    result2 = promoter.evaluate_script(script_v1, 0.89)
    print(f"  v1.0: {result2['old_status']} → {result2['new_status']} (Score: {result2['performance_score']:.1%})")
    
    print("\n📊 New Script Demotion (Primary → Secondary):")
    result3 = promoter.evaluate_script(script_v1, 0.62)
    print(f"  v1.0: {result3['old_status']} → {result3['new_status']} (Score: {result3['performance_score']:.1%})")
    
    # Get primary scripts
    primary = promoter.get_primary_scripts()
    print("\n🎯 Primary (Production) Scripts:")
    if primary:
        for script in primary:
            print(f"  {script['script_name']} v{script['version']}: {script['performance_score']:.1%}")
    else:
        print("  (No primary scripts currently)")


def example_deal_packets():
    """Example: Block 23 - Deal Packet Auto-Build."""
    print("\n" + "="*70)
    print("BLOCK 23: Deal Packet Auto-Build")
    print("="*70)
    
    builder = DealPacketBuilder()
    
    # Create lead data
    lead_1 = {
        "lead_id": "L001",
        "name": "Acme Corp",
        "value": 250000,
        "terms": "30 days, net 45",
        "source": "direct_inbound",
        "relationship_score": 0.85
    }
    
    lead_2 = {
        "lead_id": "L002",
        "name": "Widget Industries",
        "value": 500000,
        "terms": "60 days, net 30",
        "source": "referral",
        "relationship_score": 0.92
    }
    
    print("\n📦 Building Deal Packets:")
    
    # Build packets
    packet_1 = builder.build_packet(lead_1, ["Script A", "Script B"], ["Email", "SMS"])
    packet_2 = builder.build_packet(lead_2, ["Script A"], ["Email", "Phone"])
    
    print(f"  Packet 1: {packet_1}")
    print(f"  Packet 2: {packet_2}")
    
    # Retrieve and display packets
    print("\n📋 Packet Details:")
    p1_details = builder.get_packet(packet_1)
    print(f"\n  Packet 1 - {p1_details['lead_name']}:")
    print(f"    Deal Value: ${p1_details['deal_value']:,.0f}")
    print(f"    Terms: {p1_details['terms']}")
    print(f"    Scripts: {', '.join(p1_details['scripts'])}")
    print(f"    Channels: {', '.join(p1_details['channels'])}")
    print(f"    Status: {p1_details['status']}")
    
    p2_details = builder.get_packet(packet_2)
    print(f"\n  Packet 2 - {p2_details['lead_name']}:")
    print(f"    Deal Value: ${p2_details['deal_value']:,.0f}")
    print(f"    Terms: {p2_details['terms']}")
    print(f"    Scripts: {', '.join(p2_details['scripts'])}")
    print(f"    Channels: {', '.join(p2_details['channels'])}")
    print(f"    Status: {p2_details['status']}")
    
    # Update status
    builder.update_packet_status(packet_1, "in_progress")
    builder.update_packet_status(packet_2, "completed")
    
    print("\n✅ Updated packet statuses")


def example_learning_ingestion():
    """Example: Block 24 - Learning Ingestion (Allowed Sources Only)."""
    print("\n" + "="*70)
    print("BLOCK 24: Learning Ingestion Job (Allowed Sources Only)")
    print("="*70)
    
    allowed = ["Zillow", "Facebook", "Redfin", "MLS"]
    ingestor = LearningIngestor(allowed)
    
    print(f"\n✅ Allowed Sources: {', '.join(allowed)}")
    
    # Ingest from allowed sources
    print("\n📥 Ingesting from Allowed Sources:")
    
    result1 = ingestor.ingest_data("Zillow", {"leads": 150, "quality_score": 0.88})
    print(f"  Zillow: {'✅ SUCCESS' if result1['success'] else '❌ BLOCKED'} - {result1.get('data_id', result1['reason'])}")
    
    result2 = ingestor.ingest_data("Facebook", {"leads": 250, "quality_score": 0.75})
    print(f"  Facebook: {'✅ SUCCESS' if result2['success'] else '❌ BLOCKED'} - {result2.get('data_id', result2['reason'])}")
    
    result3 = ingestor.ingest_data("MLS", {"listings": 500, "quality_score": 0.92})
    print(f"  MLS: {'✅ SUCCESS' if result3['success'] else '❌ BLOCKED'} - {result3.get('data_id', result3['reason'])}")
    
    # Try ingestion from unauthorized source
    print("\n📥 Attempting Ingest from Unauthorized Source:")
    
    result4 = ingestor.ingest_data("UnknownBroker", {"leads": 100})
    print(f"  UnknownBroker: {'✅ SUCCESS' if result4['success'] else '❌ BLOCKED'} - {result4['reason']}")
    
    result5 = ingestor.ingest_data("DarkWeb", {"leads": 50})
    print(f"  DarkWeb: {'✅ SUCCESS' if result5['success'] else '❌ BLOCKED'} - {result5['reason']}")
    
    # Display blocked attempts
    blocked = ingestor.get_blocked_attempts()
    print(f"\n🚫 Blocked Attempts: {len(blocked)}")
    for attempt in blocked:
        print(f"  Source: {attempt['source']}, Reason: {attempt['reason']}")


def example_outcome_evaluation():
    """Example: Block 25 - Evaluation Loop (What Improves Outcomes)."""
    print("\n" + "="*70)
    print("BLOCK 25: Evaluation Loop (What Improves Outcomes)")
    print("="*70)
    
    evaluator = OutcomeEvaluator(baseline_threshold=0.80)
    
    print(f"\n📊 Baseline Threshold: {evaluator.baseline_threshold:.1%}")
    
    # Evaluate various metrics
    print("\n📈 Evaluating Outcomes:")
    
    metrics = [
        (0.82, "Script A - Lead Volume"),
        (0.75, "Email Channel - Conversion"),
        (0.91, "Phone Script - Close Rate"),
        (0.88, "Premium Tier - Quality"),
        (0.68, "New Territory - Ramp"),
    ]
    
    for metric, context in metrics:
        result = evaluator.evaluate_outcome(metric, context)
        status = "✅ IMPROVEMENT" if result['is_improvement'] else "⚠️  NEEDS WORK"
        print(f"  {context}: {metric:.1%} {status}")
    
    # Get improvement trend
    print("\n📊 Improvement Trend Analysis:")
    trend = evaluator.get_improvement_trend(window_size=5)
    print(f"  Trend: {trend['trend']}")
    print(f"  Improvement Rate: {trend['improvement_rate']:.1%} ({trend['improvements']}/{trend['evaluations']})")
    print(f"  Recent Metrics: {[f'{m:.1%}' for m in trend['recent_metrics']]}")


def example_model_updates():
    """Example: Block 26 - Safe Heuristic/Model Update Mechanism."""
    print("\n" + "="*70)
    print("BLOCK 26: Safe Heuristic/Model Update Mechanism")
    print("="*70)
    
    updater = SafeModelUpdater()
    
    # Create initial model
    print("\n🤖 Creating Initial Model:")
    model_id = updater.create_model("Lead Quality Scorer")
    print(f"  Model: Lead Quality Scorer v1 (ID: {model_id})")
    
    # Incremental update
    print("\n🔄 Incremental Update (v1 → v2):")
    result1 = updater.update_model(model_id, 0.87, UpdateStrategy.INCREMENTAL)
    print(f"  Accuracy: v1 → v2 ({result1['old_accuracy']:.1%} → {result1['new_accuracy']:.1%})")
    print(f"  Action: {result1['action']}")
    
    # Full retrain
    print("\n🔄 Full Retrain (v2 → v3):")
    result2 = updater.update_model(result1['new_version_id'], 0.92, UpdateStrategy.FULL_RETRAIN)
    print(f"  Accuracy: v2 → v3 ({result2['old_accuracy']:.1%} → {result2['new_accuracy']:.1%})")
    print(f"  Action: {result2['action']}")
    
    # Shadow deployment
    print("\n🔄 Shadow Deployment (v3 → v4 shadow):")
    result3 = updater.update_model(result2['new_version_id'], 0.91, UpdateStrategy.SHADOW)
    print(f"  Shadow Version: v4 ({result3['new_accuracy']:.1%})")
    print(f"  Action: {result3['action']} (inactive, testing in background)")
    
    # Check model status
    print("\n📊 Model Status:")
    status = updater.get_model_status("Lead Quality Scorer")
    print(f"  Current Version: v{status['current_version']}")
    print(f"  Accuracy: {status['accuracy']:.1%}")
    print(f"  Active: {'✅' if status['is_active'] else '⏸'}")
    print(f"  Total Versions: {status['total_versions']}")


def example_clone_readiness():
    """Example: Block 27 - Clone Readiness Scoring."""
    print("\n" + "="*70)
    print("BLOCK 27: Clone Readiness Scoring")
    print("="*70)
    
    scorer = CloneReadinessScorer(readiness_threshold=0.80)
    
    print(f"\n🎯 Readiness Threshold: {scorer.readiness_threshold:.1%}")
    
    # Score multiple clones
    print("\n🧬 Scoring Clones:")
    
    clones = [
        ("Clone-A", 0.92, 0.88, 0.85, 0.89),
        ("Clone-B", 0.85, 0.82, 0.81, 0.84),
        ("Clone-C", 0.78, 0.75, 0.72, 0.76),
        ("Clone-D", 0.95, 0.93, 0.91, 0.92),
    ]
    
    for clone_id, accuracy, confidence, consistency, robustness in clones:
        result = scorer.score_clone(clone_id, accuracy, confidence, consistency, robustness)
        status = "✅ READY" if result['is_ready'] else "⏳ NOT READY"
        print(f"  {clone_id}: {result['overall_score']:.1%} {status}")
    
    # Get ready clones
    print("\n✅ Clones Ready for Production:")
    ready = scorer.get_ready_clones()
    if ready:
        for clone in ready:
            print(f"  {clone['clone_id']}: {clone['overall_score']:.1%} (accuracy: {clone['accuracy']:.1%})")
    else:
        print("  (No clones ready yet)")


def example_clone_gates():
    """Example: Block 28 - Clone Gate Enforcement."""
    print("\n" + "="*70)
    print("BLOCK 28: Clone Gate Enforcement")
    print("="*70)
    
    enforcer = CloneGateEnforcer()
    
    # Test with passing clone
    print("\n✅ Passing Clone Through All Gates:")
    result1 = enforcer.enforce_all_gates("Clone-Production", readiness_score=0.87,
                                         accuracy=0.90, regression_detected=False)
    print(f"  Readiness: {result1['gates'][0]['status'].upper()}")
    print(f"  Performance: {result1['gates'][1]['status'].upper()}")
    print(f"  Safety: {result1['gates'][2]['status'].upper()}")
    print(f"  Decision: {result1['decision']}")
    
    # Test with failing clone
    print("\n❌ Failing Clone (Low Readiness):")
    result2 = enforcer.enforce_all_gates("Clone-Experimental", readiness_score=0.72,
                                         accuracy=0.88, regression_detected=False)
    print(f"  Readiness: {result2['gates'][0]['status'].upper()}")
    print(f"  Performance: {result2['gates'][1]['status'].upper()}")
    print(f"  Safety: {result2['gates'][2]['status'].upper()}")
    print(f"  Decision: {result2['decision']}")
    
    # Test with regression
    print("\n🔴 Safety Gate Failure (Regression Detected):")
    result3 = enforcer.enforce_all_gates("Clone-Regression", readiness_score=0.85,
                                         accuracy=0.92, regression_detected=True)
    print(f"  Readiness: {result3['gates'][0]['status'].upper()}")
    print(f"  Performance: {result3['gates'][1]['status'].upper()}")
    print(f"  Safety: {result3['gates'][2]['status'].upper()}")
    print(f"  Decision: {result3['decision']}")


def example_audit_trail():
    """Example: Block 29 - Clone Audit Trail + Rollback."""
    print("\n" + "="*70)
    print("BLOCK 29: Clone Audit Trail + Rollback")
    print("="*70)
    
    audit = CloneAuditTrail()
    
    clone_id = "Clone-Production-v2"
    
    # Log various actions
    print(f"\n📋 Logging Actions for {clone_id}:")
    
    actions = [
        ("DEPLOY", "SUCCESS", {"version": "2.0", "target": "production"}),
        ("TRAIN", "SUCCESS", {"epochs": 100, "accuracy": 0.92}),
        ("VALIDATE", "SUCCESS", {"test_cases": 1000, "pass_rate": 0.98}),
        ("GATE_CHECK", "SUCCESS", {"gates_passed": 3, "gates_failed": 0}),
        ("PROMOTE", "SUCCESS", {"from_status": "testing", "to_status": "primary"}),
    ]
    
    for action, status, details in actions:
        entry_id = audit.log_action(clone_id, action, status, details, user_id="admin@company.com")
        print(f"  {action}: {status} ✓")
    
    # Create snapshot
    print(f"\n📸 Creating Snapshot:")
    snapshot_id = audit.create_snapshot(clone_id, {"version": "2.0", "state": "production"})
    print(f"  Snapshot: {snapshot_id}")
    
    # Get audit trail
    print(f"\n📊 Complete Audit Trail:")
    trail = audit.get_audit_trail(clone_id)
    for entry in trail:
        print(f"  {entry['timestamp'].strftime('%H:%M:%S')} - {entry['action']}: {entry['status']}")


def example_verification_suite():
    """Example: Block 30 - End-to-End Brain Verification Suite."""
    print("\n" + "="*70)
    print("BLOCK 30: End-to-End Brain Verification Suite")
    print("="*70)
    
    suite = BrainVerificationSuite()
    
    print("\n🔍 Running End-to-End System Verification...")
    
    result = suite.run_full_verification()
    
    print(f"\n📊 Verification Results:")
    print(f"  Overall Status: {result['overall_status']}")
    print(f"  Total Checks: {result['total_checks']}")
    print(f"  Passed: ✅ {result['passed']}")
    print(f"  Failed: ❌ {result['failed']}")
    print(f"  Warnings: ⚠️  {result['warnings']}")
    
    print(f"\n📋 Component Status:")
    for check in result['checks']:
        status_icon = "✅" if check['status'] == 'pass' else "❌" if check['status'] == 'fail' else "⚠️"
        print(f"  {status_icon} {check['check']}: {check['message']}")


def example_integrated_workflow():
    """Example: Complete Integrated Workflow Using All Blocks."""
    print("\n" + "="*70)
    print("INTEGRATED WORKFLOW: Complete Learning + Scaling Pipeline")
    print("="*70)
    
    brain = LearningAndScalingOrchestrator(
        allowed_learning_sources=["Zillow", "Facebook", "Redfin", "MLS"]
    )
    
    print("\n🧠 Initializing Learning & Scaling Brain...")
    
    # Step 1: Set up A/B tests
    print("\n1️⃣ Step 1: Setting Up A/B Tests")
    script_a = brain.ab_tracker.register_variant("Consultative", "script")
    script_b = brain.ab_tracker.register_variant("Direct Offer", "script")
    brain.ab_tracker.track_performance(script_a, 0.84, conversions=42, cost=2100)
    brain.ab_tracker.track_performance(script_b, 0.79, conversions=39, cost=1950)
    print(f"  ✓ Registered and tracking 2 script variants")
    
    # Step 2: Ingest learning data
    print("\n2️⃣ Step 2: Ingesting Learning Data")
    brain.learning_ingestor.ingest_data("Zillow", {"leads": 150, "quality": 0.88})
    brain.learning_ingestor.ingest_data("Facebook", {"leads": 200, "quality": 0.82})
    blocked = brain.learning_ingestor.ingest_data("DarkWeb", {"leads": 10})
    print(f"  ✓ Ingested 2 allowed sources, blocked 1 unauthorized")
    
    # Step 3: Build deal packets
    print("\n3️⃣ Step 3: Building Deal Packets")
    lead_data = {"name": "Acme Corp", "value": 300000, "terms": "net 30"}
    packet_id = brain.deal_builder.build_packet(lead_data, ["Script A"], ["Email"])
    print(f"  ✓ Built deal packet for {lead_data['name']}")
    
    # Step 4: Evaluate outcomes
    print("\n4️⃣ Step 4: Evaluating Outcomes")
    brain.outcome_evaluator.evaluate_outcome(0.85, "A/B test winner")
    brain.outcome_evaluator.evaluate_outcome(0.92, "Quarterly performance")
    trend = brain.outcome_evaluator.get_improvement_trend()
    print(f"  ✓ Trend: {trend['trend']}, Improvement Rate: {trend['improvement_rate']:.1%}")
    
    # Step 5: Update models
    print("\n5️⃣ Step 5: Updating Models")
    model_id = brain.model_updater.create_model("Lead Scorer")
    brain.model_updater.update_model(model_id, 0.89, UpdateStrategy.INCREMENTAL)
    print(f"  ✓ Created and updated lead scoring model")
    
    # Step 6: Score clones
    print("\n6️⃣ Step 6: Scoring Clones for Readiness")
    brain.readiness_scorer.score_clone("Clone-Alpha", 0.91, 0.88, 0.87, 0.90)
    brain.readiness_scorer.score_clone("Clone-Beta", 0.87, 0.85, 0.84, 0.88)
    ready = brain.readiness_scorer.get_ready_clones()
    print(f"  ✓ Evaluated 2 clones, {len(ready)} ready for production")
    
    # Step 7: Enforce gates
    print("\n7️⃣ Step 7: Enforcing Clone Gates")
    gate_result = brain.gate_enforcer.enforce_all_gates("Clone-Alpha", 0.88, 0.91, False)
    print(f"  ✓ Gate enforcement: {gate_result['decision']}")
    
    # Step 8: Log audit trail
    print("\n8️⃣ Step 8: Logging Audit Trail")
    brain.audit_trail.log_action("Clone-Alpha", "DEPLOYMENT", "SUCCESS",
                                 {"version": "1.0", "target": "prod"})
    print(f"  ✓ Logged deployment action")
    
    # Step 9: Run verification
    print("\n9️⃣ Step 9: Running System Verification")
    verification = brain.run_verification()
    print(f"  ✓ System verification: {verification['overall_status']}")
    print(f"    Passed: {verification['passed']}, Failed: {verification['failed']}")
    
    # Step 10: Get final status
    print("\n🔟 Step 10: Final System Status")
    status = brain.get_status()
    print(f"  A/B Variants: {status['ab_variants']}")
    print(f"  Scripts: {status['scripts']}")
    print(f"  Deal Packets: {status['deal_packets']}")
    print(f"  Ingested Datasets: {status['ingested_datasets']}")
    print(f"  Evaluations: {status['evaluations']}")
    print(f"  Models: {status['models']}")
    print(f"  Clone Scores: {status['clone_scores']}")
    print(f"  Audit Entries: {status['audit_entries']}")
    
    print("\n✅ INTEGRATED WORKFLOW COMPLETE")


# Import needed for examples
from services.learning_and_scaling import UpdateStrategy


if __name__ == "__main__":
    """Run all examples."""
    print("\n")
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  BATCH 3: LEARNING + SCALING SAFETY - COMPLETE EXAMPLES".center(68) + "█")
    print("█" + "  Activation Blocks 21-30".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    # Run all examples
    example_ab_tracking()
    example_script_promotion()
    example_deal_packets()
    example_learning_ingestion()
    example_outcome_evaluation()
    example_model_updates()
    example_clone_readiness()
    example_clone_gates()
    example_audit_trail()
    example_verification_suite()
    example_integrated_workflow()
    
    print("\n")
    print("█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  ALL EXAMPLES COMPLETED SUCCESSFULLY".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    print()
