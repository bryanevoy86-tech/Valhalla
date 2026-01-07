"""
Test Suite for Batch 3 - Learning + Scaling Safety
50+ unit tests for all 10 activation blocks
"""

import unittest
from datetime import datetime, timedelta
from services.learning_and_scaling import (
    ABTracker, ScriptPromoter, ScriptStatus, DealPacketBuilder,
    LearningIngestor, OutcomeEvaluator, SafeModelUpdater, UpdateStrategy,
    CloneReadinessScorer, CloneGateEnforcer, CloneAuditTrail,
    BrainVerificationSuite, LearningAndScalingOrchestrator
)


class TestABTracker(unittest.TestCase):
    """Tests for A/B Tracking (Block 21)."""
    
    def setUp(self):
        self.tracker = ABTracker()
    
    def test_register_variant(self):
        """Test registering A/B variant."""
        var_id = self.tracker.register_variant("Test Script", "script")
        self.assertIsNotNone(var_id)
        self.assertIn("var_", var_id)
    
    def test_track_performance(self):
        """Test tracking performance."""
        var_id = self.tracker.register_variant("Test", "script")
        result = self.tracker.track_performance(var_id, 0.85, conversions=10)
        self.assertEqual(result['performance'], 0.85)
        self.assertIsNotNone(result['conversion_rate'])
    
    def test_get_winning_variant(self):
        """Test finding winning variant."""
        var1 = self.tracker.register_variant("Poor", "script")
        var2 = self.tracker.register_variant("Good", "script")
        self.tracker.track_performance(var1, 0.60)
        self.tracker.track_performance(var2, 0.90)
        
        winner = self.tracker.get_winning_variant("script")
        self.assertEqual(winner['variant_name'], "Good")
    
    def test_compare_variants(self):
        """Test comparing variants."""
        var1 = self.tracker.register_variant("A", "script")
        var2 = self.tracker.register_variant("B", "script")
        self.tracker.track_performance(var1, 0.70)
        self.tracker.track_performance(var2, 0.80)
        
        comparison = self.tracker.compare_variants([var1, var2])
        self.assertEqual(len(comparison), 2)
        self.assertGreater(comparison[0]['performance'], comparison[1]['performance'])


class TestScriptPromoter(unittest.TestCase):
    """Tests for Script Promotion (Block 22)."""
    
    def setUp(self):
        self.promoter = ScriptPromoter()
    
    def test_register_script(self):
        """Test registering script."""
        script_id = self.promoter.register_script("Test", "1.0")
        self.assertIsNotNone(script_id)
    
    def test_promote_experimental_to_testing(self):
        """Test promotion Experimental → Testing."""
        script_id = self.promoter.register_script("Test", "1.0")
        result = self.promoter.evaluate_script(script_id, 0.87)
        self.assertEqual(result['new_status'], ScriptStatus.TESTING.value)
    
    def test_promote_testing_to_primary(self):
        """Test promotion Testing → Primary."""
        script_id = self.promoter.register_script("Test", "1.0")
        self.promoter.evaluate_script(script_id, 0.87)  # Exp → Testing
        result = self.promoter.evaluate_script(script_id, 0.89)  # Testing → Primary
        self.assertEqual(result['new_status'], ScriptStatus.PRIMARY.value)
    
    def test_demote_on_low_score(self):
        """Test demotion on low performance."""
        script_id = self.promoter.register_script("Test", "1.0")
        self.promoter.evaluate_script(script_id, 0.87)
        self.promoter.evaluate_script(script_id, 0.89)  # Now primary
        result = self.promoter.evaluate_script(script_id, 0.60)  # Drop to secondary
        self.assertEqual(result['new_status'], ScriptStatus.SECONDARY.value)
    
    def test_get_primary_scripts(self):
        """Test retrieving primary scripts."""
        s1 = self.promoter.register_script("A", "1.0")
        s2 = self.promoter.register_script("B", "1.0")
        
        self.promoter.evaluate_script(s1, 0.87)
        self.promoter.evaluate_script(s1, 0.89)  # Primary
        self.promoter.evaluate_script(s2, 0.70)  # Testing
        
        primary = self.promoter.get_primary_scripts()
        self.assertEqual(len(primary), 1)


class TestDealPacketBuilder(unittest.TestCase):
    """Tests for Deal Packets (Block 23)."""
    
    def setUp(self):
        self.builder = DealPacketBuilder()
    
    def test_build_packet(self):
        """Test building deal packet."""
        lead = {"name": "John", "value": 100000, "terms": "30 days"}
        packet_id = self.builder.build_packet(lead, ["Script A"], ["Email"])
        self.assertIsNotNone(packet_id)
    
    def test_get_packet(self):
        """Test retrieving packet."""
        lead = {"name": "John", "value": 100000, "terms": "30 days"}
        packet_id = self.builder.build_packet(lead, ["Script A"], ["Email"])
        packet = self.builder.get_packet(packet_id)
        
        self.assertIsNotNone(packet)
        self.assertEqual(packet['lead_name'], "John")
        self.assertEqual(packet['deal_value'], 100000)
    
    def test_update_packet_status(self):
        """Test updating packet status."""
        lead = {"name": "John", "value": 100000}
        packet_id = self.builder.build_packet(lead, ["Script A"], ["Email"])
        
        success = self.builder.update_packet_status(packet_id, "in_progress")
        self.assertTrue(success)
        
        packet = self.builder.get_packet(packet_id)
        self.assertEqual(packet['status'], "in_progress")
    
    def test_export_packet(self):
        """Test exporting packet."""
        lead = {"name": "John", "value": 100000}
        packet_id = self.builder.build_packet(lead, ["Script A"], ["Email"])
        
        export = self.builder.export_packet(packet_id, format_type='json')
        self.assertIsNotNone(export)
        self.assertIn("John", export)


class TestLearningIngestor(unittest.TestCase):
    """Tests for Learning Ingestion (Block 24)."""
    
    def setUp(self):
        self.ingestor = LearningIngestor(["Source A", "Source B"])
    
    def test_ingest_allowed_source(self):
        """Test ingesting from allowed source."""
        result = self.ingestor.ingest_data("Source A", {"data": "test"})
        self.assertTrue(result['success'])
    
    def test_block_unauthorized_source(self):
        """Test blocking unauthorized source."""
        result = self.ingestor.ingest_data("UnknownSource", {"data": "test"})
        self.assertFalse(result['success'])
        self.assertIn("not allowed", result['reason'])
    
    def test_get_blocked_attempts(self):
        """Test retrieving blocked attempts."""
        self.ingestor.ingest_data("BadSource1", {})
        self.ingestor.ingest_data("BadSource2", {})
        
        blocked = self.ingestor.get_blocked_attempts()
        self.assertEqual(len(blocked), 2)
    
    def test_add_allowed_source(self):
        """Test adding source to whitelist."""
        self.ingestor.add_allowed_source("Source C")
        result = self.ingestor.ingest_data("Source C", {"data": "test"})
        self.assertTrue(result['success'])
    
    def test_remove_allowed_source(self):
        """Test removing source from whitelist."""
        self.ingestor.remove_allowed_source("Source A")
        result = self.ingestor.ingest_data("Source A", {"data": "test"})
        self.assertFalse(result['success'])


class TestOutcomeEvaluator(unittest.TestCase):
    """Tests for Outcome Evaluation (Block 25)."""
    
    def setUp(self):
        self.evaluator = OutcomeEvaluator(baseline_threshold=0.80)
    
    def test_evaluate_above_threshold(self):
        """Test evaluation above threshold."""
        result = self.evaluator.evaluate_outcome(0.85)
        self.assertTrue(result['is_improvement'])
    
    def test_evaluate_below_threshold(self):
        """Test evaluation below threshold."""
        result = self.evaluator.evaluate_outcome(0.75)
        self.assertFalse(result['is_improvement'])
    
    def test_improvement_trend(self):
        """Test improvement trend."""
        for metric in [0.82, 0.85, 0.88, 0.87, 0.86]:
            self.evaluator.evaluate_outcome(metric)
        
        trend = self.evaluator.get_improvement_trend(window_size=5)
        self.assertEqual(trend['evaluations'], 5)
        self.assertGreater(trend['improvement_rate'], 0)
    
    def test_set_baseline_threshold(self):
        """Test changing baseline threshold."""
        self.evaluator.set_baseline_threshold(0.90)
        result = self.evaluator.evaluate_outcome(0.85)
        self.assertFalse(result['is_improvement'])


class TestSafeModelUpdater(unittest.TestCase):
    """Tests for Model Updates (Block 26)."""
    
    def setUp(self):
        self.updater = SafeModelUpdater()
    
    def test_create_model(self):
        """Test creating model."""
        model_id = self.updater.create_model("Test Model")
        self.assertIsNotNone(model_id)
    
    def test_update_model_incremental(self):
        """Test incremental update."""
        model_id = self.updater.create_model("Test")
        result = self.updater.update_model(model_id, 0.88, UpdateStrategy.INCREMENTAL)
        self.assertEqual(result['action'], 'PROMOTED')
    
    def test_update_model_shadow(self):
        """Test shadow deployment."""
        model_id = self.updater.create_model("Test")
        result = self.updater.update_model(model_id, 0.90, UpdateStrategy.SHADOW)
        self.assertEqual(result['action'], 'SHADOW_DEPLOYED')
    
    def test_rollback_model(self):
        """Test model rollback."""
        model_id = self.updater.create_model("Test")
        self.updater.update_model(model_id, 0.88, UpdateStrategy.INCREMENTAL)
        
        result = self.updater.rollback_model("Test")
        self.assertEqual(result['rolled_back_from'], 2)
        self.assertEqual(result['rolled_back_to'], 1)
    
    def test_get_model_status(self):
        """Test getting model status."""
        self.updater.create_model("Test")
        status = self.updater.get_model_status("Test")
        
        self.assertIsNotNone(status)
        self.assertEqual(status['current_version'], 1)


class TestCloneReadinessScorer(unittest.TestCase):
    """Tests for Clone Readiness (Block 27)."""
    
    def setUp(self):
        self.scorer = CloneReadinessScorer(readiness_threshold=0.80)
    
    def test_score_clone_ready(self):
        """Test scoring ready clone."""
        result = self.scorer.score_clone("clone_1", 0.90, 0.85, 0.88, 0.87)
        self.assertTrue(result['is_ready'])
        self.assertGreater(result['overall_score'], 0.80)
    
    def test_score_clone_not_ready(self):
        """Test scoring unready clone."""
        result = self.scorer.score_clone("clone_2", 0.70, 0.72, 0.68, 0.75)
        self.assertFalse(result['is_ready'])
    
    def test_get_ready_clones(self):
        """Test getting ready clones."""
        self.scorer.score_clone("clone_1", 0.90, 0.85, 0.88, 0.87)
        self.scorer.score_clone("clone_2", 0.70, 0.72, 0.68, 0.75)
        
        ready = self.scorer.get_ready_clones()
        self.assertEqual(len(ready), 1)
    
    def test_composite_score_calculation(self):
        """Test composite score calculation."""
        result = self.scorer.score_clone("clone", 0.80, 0.80, 0.80, 0.80)
        # Expected: 0.4*0.8 + 0.3*0.8 + 0.2*0.8 + 0.1*0.8 = 0.80
        self.assertEqual(result['overall_score'], 0.80)


class TestCloneGateEnforcer(unittest.TestCase):
    """Tests for Clone Gates (Block 28)."""
    
    def setUp(self):
        self.enforcer = CloneGateEnforcer()
    
    def test_readiness_gate_pass(self):
        """Test readiness gate pass."""
        result = self.enforcer.check_readiness_gate("clone_1", 0.85)
        self.assertEqual(result['status'], 'pass')
    
    def test_readiness_gate_fail(self):
        """Test readiness gate fail."""
        result = self.enforcer.check_readiness_gate("clone_1", 0.75)
        self.assertEqual(result['status'], 'fail')
    
    def test_performance_gate_pass(self):
        """Test performance gate pass."""
        result = self.enforcer.check_performance_gate("clone_1", 0.87, threshold=0.85)
        self.assertEqual(result['status'], 'pass')
    
    def test_safety_gate_no_regression(self):
        """Test safety gate with no regression."""
        result = self.enforcer.check_safety_gate("clone_1", regression_detected=False)
        self.assertEqual(result['status'], 'pass')
    
    def test_enforce_all_gates_pass(self):
        """Test all gates pass."""
        result = self.enforcer.enforce_all_gates("clone_1", 0.85, 0.90, False)
        self.assertTrue(result['can_promote'])
        self.assertEqual(result['decision'], 'PROMOTE')
    
    def test_enforce_all_gates_fail(self):
        """Test all gates fail."""
        result = self.enforcer.enforce_all_gates("clone_1", 0.75, 0.80, True)
        self.assertFalse(result['can_promote'])
        self.assertEqual(result['decision'], 'BLOCK')


class TestCloneAuditTrail(unittest.TestCase):
    """Tests for Audit Trail (Block 29)."""
    
    def setUp(self):
        self.audit = CloneAuditTrail()
    
    def test_log_action(self):
        """Test logging action."""
        entry_id = self.audit.log_action("clone_1", "DEPLOY", "SUCCESS", {"version": "1.0"})
        self.assertIsNotNone(entry_id)
    
    def test_get_audit_trail(self):
        """Test retrieving audit trail."""
        self.audit.log_action("clone_1", "DEPLOY", "SUCCESS", {})
        self.audit.log_action("clone_1", "TRAIN", "SUCCESS", {})
        
        trail = self.audit.get_audit_trail("clone_1")
        self.assertEqual(len(trail), 2)
    
    def test_create_snapshot(self):
        """Test creating snapshot."""
        snapshot_id = self.audit.create_snapshot("clone_1", {"state": "active"})
        self.assertIsNotNone(snapshot_id)
    
    def test_export_audit_trail(self):
        """Test exporting audit trail."""
        self.audit.log_action("clone_1", "DEPLOY", "SUCCESS", {})
        export = self.audit.export_audit_trail("clone_1", format_type='json')
        self.assertIsNotNone(export)


class TestBrainVerificationSuite(unittest.TestCase):
    """Tests for Verification Suite (Block 30)."""
    
    def setUp(self):
        self.suite = BrainVerificationSuite()
    
    def test_verify_ab_tracking(self):
        """Test A/B tracking verification."""
        result = self.suite.verify_ab_tracking()
        self.assertEqual(result['status'], 'pass')
    
    def test_verify_script_promotion(self):
        """Test script promotion verification."""
        result = self.suite.verify_script_promotion()
        self.assertEqual(result['status'], 'pass')
    
    def test_verify_deal_packets(self):
        """Test deal packets verification."""
        result = self.suite.verify_deal_packets()
        self.assertEqual(result['status'], 'pass')
    
    def test_verify_learning_ingestion(self):
        """Test learning ingestion verification."""
        result = self.suite.verify_learning_ingestion()
        self.assertEqual(result['status'], 'pass')
    
    def test_verify_outcome_evaluation(self):
        """Test outcome evaluation verification."""
        result = self.suite.verify_outcome_evaluation()
        self.assertEqual(result['status'], 'pass')
    
    def test_run_full_verification(self):
        """Test full verification suite."""
        result = self.suite.run_full_verification()
        self.assertIn(result['overall_status'], ['PASS', 'FAIL'])
        self.assertGreater(result['total_checks'], 0)
    
    def test_get_verification_report(self):
        """Test getting verification report."""
        self.suite.verify_ab_tracking()
        report = self.suite.get_verification_report(format_type='json')
        self.assertIsNotNone(report)


class TestLearningAndScalingOrchestrator(unittest.TestCase):
    """Tests for Main Orchestrator."""
    
    def setUp(self):
        self.brain = LearningAndScalingOrchestrator()
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initializes all components."""
        self.assertIsNotNone(self.brain.ab_tracker)
        self.assertIsNotNone(self.brain.script_promoter)
        self.assertIsNotNone(self.brain.deal_builder)
    
    def test_get_status(self):
        """Test getting orchestrator status."""
        status = self.brain.get_status()
        self.assertIn('ab_variants', status)
        self.assertIn('scripts', status)
        self.assertIn('deal_packets', status)
    
    def test_run_verification(self):
        """Test running verification through orchestrator."""
        result = self.brain.run_verification()
        self.assertIn('overall_status', result)


class TestIntegration(unittest.TestCase):
    """Integration tests for Batch 3."""
    
    def test_complete_workflow(self):
        """Test complete workflow with all components."""
        brain = LearningAndScalingOrchestrator()
        
        # A/B tracking
        var_id = brain.ab_tracker.register_variant("Test", "script")
        brain.ab_tracker.track_performance(var_id, 0.85)
        
        # Script promotion
        script_id = brain.script_promoter.register_script("Test", "1.0")
        brain.script_promoter.evaluate_script(script_id, 0.87)
        
        # Deal packets
        lead = {"name": "Test", "value": 100000}
        packet_id = brain.deal_builder.build_packet(lead, ["Script A"], ["Email"])
        
        # Ingest learning
        brain.learning_ingestor.ingest_data("Zillow", {"leads": 100})
        
        # Evaluate outcomes
        brain.outcome_evaluator.evaluate_outcome(0.85)
        
        # Update models
        model_id = brain.model_updater.create_model("Test")
        brain.model_updater.update_model(model_id, 0.88, UpdateStrategy.INCREMENTAL)
        
        # Score clones
        brain.readiness_scorer.score_clone("clone_1", 0.90, 0.88, 0.87, 0.89)
        
        # Run gates
        brain.gate_enforcer.enforce_all_gates("clone_1", 0.85, 0.90, False)
        
        # Log audit
        brain.audit_trail.log_action("clone_1", "DEPLOY", "SUCCESS", {})
        
        # Verify system
        result = brain.run_verification()
        self.assertIn('overall_status', result)
        
        # Check status
        status = brain.get_status()
        self.assertGreater(status['ab_variants'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
