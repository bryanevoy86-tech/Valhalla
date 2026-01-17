"""
Test suite for Batch 2 - Brain Intelligence + Deal Quality Components
Tests all 10 activation blocks (11-20)
"""

import unittest
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


class TestSourceRegistry(unittest.TestCase):
    """Tests for SourceRegistry."""
    
    def setUp(self):
        self.registry = SourceRegistry()
    
    def test_add_source(self):
        """Test adding source to registry."""
        source = self.registry.add_source(
            "Zillow",
            SourceType.PUBLIC_LISTING,
            0.3,
            0.05
        )
        self.assertIsNotNone(source)
        self.assertEqual(source.source_name, "Zillow")
    
    def test_get_source(self):
        """Test retrieving source."""
        self.registry.add_source("MLS", SourceType.MLS, 0.2, 0.15)
        source = self.registry.get_source("MLS")
        self.assertIsNotNone(source)
        self.assertEqual(source.risk_score, 0.2)
    
    def test_source_not_found(self):
        """Test retrieving non-existent source."""
        source = self.registry.get_source("NonExistent")
        self.assertIsNone(source)
    
    def test_update_source(self):
        """Test updating source."""
        self.registry.add_source("Portal", SourceType.PORTAL, 0.4, 0.08)
        self.registry.update_source("Portal", risk_score=0.35)
        source = self.registry.get_source("Portal")
        self.assertEqual(source.risk_score, 0.35)
    
    def test_list_sources(self):
        """Test listing sources."""
        self.registry.add_source("Source1", SourceType.MLS, 0.2, 0.1)
        self.registry.add_source("Source2", SourceType.SOCIAL, 0.5, 0.05)
        sources = self.registry.list_sources()
        self.assertEqual(len(sources), 2)
    
    def test_get_active_sources(self):
        """Test getting active sources."""
        s1 = self.registry.add_source("Active", SourceType.MLS, 0.2, 0.1)
        s2 = self.registry.add_source("Inactive", SourceType.SOCIAL, 0.5, 0.05)
        s2.is_active = False
        
        active = self.registry.get_active_sources()
        self.assertEqual(len(active), 1)


class TestSourceQualityScorer(unittest.TestCase):
    """Tests for SourceQualityScorer."""
    
    def setUp(self):
        self.registry = SourceRegistry()
        self.scorer = SourceQualityScorer(self.registry)
    
    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        self.registry.add_source("MLS", SourceType.MLS, 0.2, 0.20)
        score = self.scorer.calculate_quality_score("MLS")
        self.assertIsNotNone(score)
        self.assertGreater(score, 0)
        self.assertLess(score, 1)
    
    def test_score_none_for_missing_source(self):
        """Test score returns None for missing source."""
        score = self.scorer.calculate_quality_score("NonExistent")
        self.assertIsNone(score)
    
    def test_rank_sources(self):
        """Test ranking sources by quality."""
        self.registry.add_source("High", SourceType.MLS, 0.1, 0.30)
        self.registry.add_source("Low", SourceType.SOCIAL, 0.7, 0.05)
        
        ranked = self.scorer.rank_sources()
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0][0], "High")
        self.assertGreater(ranked[0][1], ranked[1][1])


class TestSourceLifecycleManager(unittest.TestCase):
    """Tests for SourceLifecycleManager."""
    
    def setUp(self):
        self.registry = SourceRegistry()
        self.scorer = SourceQualityScorer(self.registry)
        self.lifecycle = SourceLifecycleManager(self.registry, self.scorer)
    
    def test_evaluate_source_health_good(self):
        """Test health evaluation for good source."""
        self.registry.add_source("Good", SourceType.MLS, 0.1, 0.25)
        result = self.lifecycle.evaluate_source_health("Good")
        self.assertFalse(result['is_escalated'])
    
    def test_evaluate_source_health_pause(self):
        """Test health evaluation triggers pause."""
        self.registry.add_source("Bad", SourceType.SOCIAL, 0.8, 0.02)
        self.lifecycle.set_thresholds(pause=0.3, kill=0.1)
        result = self.lifecycle.evaluate_source_health("Bad")
        self.assertTrue(result['is_escalated'])


class TestMarketRegistry(unittest.TestCase):
    """Tests for MarketRegistry."""
    
    def setUp(self):
        self.market = MarketRegistry()
    
    def test_add_zone(self):
        """Test adding market zone."""
        zone = self.market.add_zone("SF", 1500000, 0.7)
        self.assertIsNotNone(zone)
        self.assertEqual(zone.zone_name, "SF")
    
    def test_get_zone(self):
        """Test retrieving zone."""
        self.market.add_zone("Austin", 600000, 0.5)
        zone = self.market.get_zone("Austin")
        self.assertIsNotNone(zone)
        self.assertEqual(zone.average_price, 600000)
    
    def test_update_zone(self):
        """Test updating zone."""
        self.market.add_zone("NYC", 800000, 0.6)
        self.market.update_zone("NYC", zone_risk_factor=0.55)
        zone = self.market.get_zone("NYC")
        self.assertEqual(zone.zone_risk_factor, 0.55)


class TestDealCapCalculator(unittest.TestCase):
    """Tests for DealCapCalculator."""
    
    def setUp(self):
        self.market = MarketRegistry()
        self.calculator = DealCapCalculator(self.market)
    
    def test_calculate_deal_cap_basic(self):
        """Test basic deal cap calculation."""
        self.market.add_zone("Zone1", 1000000, 0.5)
        cap = self.calculator.calculate_deal_cap("Zone1", method='basic')
        expected = 1000000 * (1 - 0.5)
        self.assertEqual(cap, expected)
    
    def test_calculate_deal_cap_demand_adjusted(self):
        """Test demand-adjusted cap."""
        self.market.add_zone("Zone2", 1000000, 0.5, demand_factor=0.8)
        cap = self.calculator.calculate_deal_cap("Zone2", method='demand_adjusted')
        self.assertIsNotNone(cap)
        self.assertGreater(cap, 0)
    
    def test_cap_none_for_missing_zone(self):
        """Test cap returns None for missing zone."""
        cap = self.calculator.calculate_deal_cap("NonExistent")
        self.assertIsNone(cap)


class TestDuplicateResolver(unittest.TestCase):
    """Tests for DuplicateResolver."""
    
    def setUp(self):
        self.resolver = DuplicateResolver()
    
    def test_no_duplicates(self):
        """Test with no duplicates."""
        leads = [
            {"email": "john@test.com", "name": "John"},
            {"email": "jane@test.com", "name": "Jane"},
        ]
        unique = self.resolver.resolve_duplicates(leads)
        self.assertEqual(len(unique), 2)
    
    def test_with_duplicates(self):
        """Test with duplicates."""
        leads = [
            {"email": "john@test.com", "name": "John", "phone": "111"},
            {"email": "john@test.com", "name": "John", "phone": None},
        ]
        unique = self.resolver.resolve_duplicates(leads)
        self.assertEqual(len(unique), 1)
    
    def test_merge_leads_fills_missing(self):
        """Test merge fills missing fields."""
        leads = [
            {"email": "john@test.com", "phone": "111", "address": None},
            {"email": "john@test.com", "phone": None, "address": "123 Main"},
        ]
        unique = self.resolver.resolve_duplicates(leads)
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0]['phone'], "111")
        self.assertEqual(unique[0]['address'], "123 Main")


class TestStageEscalationEngine(unittest.TestCase):
    """Tests for StageEscalationEngine."""
    
    def setUp(self):
        self.escalator = StageEscalationEngine()
    
    def test_lead_not_escalated(self):
        """Test lead not escalated when within threshold."""
        lead = {"name": "John", "stage": "lead", "stage_duration_days": 3}
        result = self.escalator.evaluate_lead_progression(lead)
        self.assertFalse(result['is_escalated'])
    
    def test_lead_escalated(self):
        """Test lead escalated when exceeding threshold."""
        lead = {"name": "John", "stage": "lead", "stage_duration_days": 10}
        result = self.escalator.evaluate_lead_progression(lead)
        self.assertTrue(result['is_escalated'])
    
    def test_escalation_priority(self):
        """Test escalation priority calculation."""
        lead = {"name": "John", "stage": "lead", "stage_duration_days": 25}
        result = self.escalator.evaluate_lead_progression(lead)
        self.assertEqual(result['priority'], 'critical')
    
    def test_set_threshold(self):
        """Test setting custom threshold."""
        self.escalator.set_threshold('lead', 10)
        lead = {"name": "John", "stage": "lead", "stage_duration_days": 9}
        result = self.escalator.evaluate_lead_progression(lead)
        self.assertFalse(result['is_escalated'])


class TestConePrioritizer(unittest.TestCase):
    """Tests for ConePrioritizer."""
    
    def setUp(self):
        self.prioritizer = ConePrioritizer()
    
    def test_prioritize_leads(self):
        """Test lead prioritization."""
        leads = [
            {"name": "L1", "deal_size_score": 0.3, "conversion_likelihood": 0.3, "timeline_score": 0.3, "relationship_strength": 0.3},
            {"name": "L2", "deal_size_score": 0.9, "conversion_likelihood": 0.9, "timeline_score": 0.9, "relationship_strength": 0.9},
        ]
        top = self.prioritizer.prioritize_leads(leads, top_n=1)
        self.assertEqual(len(top), 1)
        self.assertEqual(top[0]['name'], 'L2')
    
    def test_top_n_limit(self):
        """Test top-N limit."""
        leads = [
            {"name": f"L{i}", "deal_size_score": 0.5, "conversion_likelihood": 0.5, "timeline_score": 0.5, "relationship_strength": 0.5}
            for i in range(20)
        ]
        top = self.prioritizer.prioritize_leads(leads, top_n=10)
        self.assertEqual(len(top), 10)


class TestShieldMonitor(unittest.TestCase):
    """Tests for ShieldMonitor."""
    
    def setUp(self):
        self.shield = ShieldMonitor()
    
    def test_register_shield(self):
        """Test registering shield."""
        self.shield.register_shield("Risk", 0.6, 0.8)
        self.assertIn("Risk", self.shield.shields)
    
    def test_shield_safe_value(self):
        """Test safe shield value."""
        self.shield.register_shield("Risk", 0.6, 0.8)
        alert = self.shield.update_shield_value("Risk", 0.5)
        self.assertEqual(alert, ShieldMonitor.ShieldAlert.SAFE)
    
    def test_shield_warning(self):
        """Test warning alert."""
        self.shield.register_shield("Risk", 0.6, 0.8)
        alert = self.shield.update_shield_value("Risk", 0.65)
        self.assertEqual(alert, ShieldMonitor.ShieldAlert.WARNING)
    
    def test_shield_critical(self):
        """Test critical alert."""
        self.shield.register_shield("Risk", 0.6, 0.8)
        alert = self.shield.update_shield_value("Risk", 0.85)
        self.assertEqual(alert, ShieldMonitor.ShieldAlert.CRITICAL)


class TestDecisionLogger(unittest.TestCase):
    """Tests for DecisionLogger."""
    
    def setUp(self):
        self.logger = DecisionLogger()
    
    def test_log_decision(self):
        """Test logging decision."""
        dec_id = self.logger.log_decision(
            "Lead Score",
            DecisionLogger.DecisionCategory.LEAD_SCORING,
            "High conversion potential"
        )
        self.assertIsNotNone(dec_id)
    
    def test_get_decision(self):
        """Test retrieving decision."""
        dec_id = self.logger.log_decision(
            "Test",
            DecisionLogger.DecisionCategory.OTHER,
            "Test reason"
        )
        decision = self.logger.get_decision(dec_id)
        self.assertEqual(decision['type'], 'Test')
    
    def test_get_decisions_by_type(self):
        """Test filtering decisions by type."""
        self.logger.log_decision("Type1", DecisionLogger.DecisionCategory.LEAD_SCORING, "Reason1")
        self.logger.log_decision("Type1", DecisionLogger.DecisionCategory.LEAD_SCORING, "Reason2")
        self.logger.log_decision("Type2", DecisionLogger.DecisionCategory.DEAL_APPROVAL, "Reason3")
        
        decisions = self.logger.get_decisions_by_type("Type1")
        self.assertEqual(len(decisions), 2)
    
    def test_export_decisions(self):
        """Test exporting decisions."""
        self.logger.log_decision("Test", DecisionLogger.DecisionCategory.OTHER, "Reason")
        export = self.logger.export_decisions(format='json')
        self.assertIsInstance(export, str)
        self.assertIn("Test", export)


class TestBrainIntelligenceOrchestrator(unittest.TestCase):
    """Tests for BrainIntelligenceOrchestrator."""
    
    def setUp(self):
        self.brain = BrainIntelligenceOrchestrator()
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initializes all components."""
        self.assertIsNotNone(self.brain.source_registry)
        self.assertIsNotNone(self.brain.market_registry)
        self.assertIsNotNone(self.brain.decision_logger)
    
    def test_get_status(self):
        """Test getting orchestrator status."""
        status = self.brain.get_status()
        self.assertIn('sources_count', status)
        self.assertIn('zones_count', status)
    
    def test_analyze_deal(self):
        """Test deal analysis."""
        self.brain.source_registry.add_source("MLS", SourceType.MLS, 0.2, 0.15)
        self.brain.market_registry.add_zone("Austin", 600000, 0.5)
        
        deal = {
            "id": "D1",
            "source": "MLS",
            "zone": "Austin",
            "deal_size_score": 0.7,
            "conversion_likelihood": 0.8,
            "timeline_score": 0.6,
            "relationship_strength": 0.7
        }
        
        analysis = self.brain.analyze_deal(deal)
        self.assertEqual(analysis['deal_id'], "D1")
        self.assertIn('components', analysis)


class TestIntegration(unittest.TestCase):
    """Integration tests for Batch 2."""
    
    def test_complete_workflow(self):
        """Test complete workflow with all components."""
        brain = BrainIntelligenceOrchestrator()
        
        # Add sources
        brain.source_registry.add_source("MLS", SourceType.MLS, 0.2, 0.2)
        
        # Add zones
        brain.market_registry.add_zone("Austin", 600000, 0.5)
        
        # Resolve duplicates
        leads = [
            {"email": "john@test.com", "name": "John"},
            {"email": "john@test.com", "name": "John"},
        ]
        unique = brain.duplicate_resolver.resolve_duplicates(leads)
        self.assertEqual(len(unique), 1)
        
        # Prioritize leads
        leads = [
            {"name": "L1", "deal_size_score": 0.5, "conversion_likelihood": 0.5, "timeline_score": 0.5, "relationship_strength": 0.5}
        ]
        brain.cone_prioritizer.prioritize_leads(leads)
        
        # Get status
        status = brain.get_status()
        self.assertGreater(status['sources_count'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
