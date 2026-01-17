"""
Batch 2: Brain Intelligence + Deal Quality Implementation
10 Activation Blocks (11-20) for lead source intelligence and deal quality
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ============================================================================
# 11. SOURCE REGISTRY (Profiles per Lead Source)
# ============================================================================

class SourceType(Enum):
    """Enumeration of source types."""
    PUBLIC_LISTING = "public_listing"
    PRIVATE_LISTING = "private_listing"
    MLS = "mls"
    PORTAL = "portal"
    DIRECT = "direct"
    REFERRAL = "referral"
    SOCIAL = "social"
    OTHER = "other"


class SourceProfile:
    """Profile for a lead source."""
    
    def __init__(
        self,
        source_name: str,
        source_type: SourceType,
        risk_score: float,
        conversion_rate: float,
        volume_monthly: int = 0,
        cost_per_lead: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        """
        Initialize source profile.
        
        Args:
            source_name: Name of the lead source
            source_type: Type of source
            risk_score: Risk score (0-1, higher = more risky)
            conversion_rate: Expected conversion rate (0-1)
            volume_monthly: Expected monthly lead volume
            cost_per_lead: Cost per lead from this source
            metadata: Additional metadata
        """
        self.source_name = source_name
        self.source_type = source_type
        self.risk_score = max(0, min(1, risk_score))
        self.conversion_rate = max(0, min(1, conversion_rate))
        self.volume_monthly = volume_monthly
        self.cost_per_lead = cost_per_lead
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.is_active = True
        self.performance_history: List[Dict] = []
        
        logger.info(
            f"Source profile created: {source_name} "
            f"(type={source_type.value}, risk={risk_score}, conv={conversion_rate})"
        )
    
    def update_performance(self, leads_received: int, conversions: int):
        """Update performance history."""
        actual_conversion = conversions / leads_received if leads_received > 0 else 0
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'leads_received': leads_received,
            'conversions': conversions,
            'actual_conversion_rate': actual_conversion
        })
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'source_name': self.source_name,
            'source_type': self.source_type.value,
            'risk_score': self.risk_score,
            'conversion_rate': self.conversion_rate,
            'volume_monthly': self.volume_monthly,
            'cost_per_lead': self.cost_per_lead,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


class SourceRegistry:
    """Registry for managing lead source profiles."""
    
    def __init__(self):
        """Initialize source registry."""
        self.sources: Dict[str, SourceProfile] = {}
        self.logger = logger
    
    def add_source(
        self,
        source_name: str,
        source_type: SourceType,
        risk_score: float,
        conversion_rate: float,
        **kwargs
    ) -> SourceProfile:
        """Add new source profile."""
        profile = SourceProfile(
            source_name,
            source_type,
            risk_score,
            conversion_rate,
            **kwargs
        )
        self.sources[source_name] = profile
        self.logger.info(f"Added source: {source_name}")
        return profile
    
    def get_source(self, source_name: str) -> Optional[SourceProfile]:
        """Get source profile."""
        return self.sources.get(source_name)
    
    def update_source(self, source_name: str, **kwargs) -> Optional[SourceProfile]:
        """Update source profile."""
        profile = self.sources.get(source_name)
        if profile:
            for key, value in kwargs.items():
                if hasattr(profile, key) and not key.startswith('_'):
                    setattr(profile, key, value)
            profile.updated_at = datetime.now()
        return profile
    
    def list_sources(self) -> List[SourceProfile]:
        """List all sources."""
        return list(self.sources.values())
    
    def get_active_sources(self) -> List[SourceProfile]:
        """Get all active sources."""
        return [s for s in self.sources.values() if s.is_active]


# ============================================================================
# 12. SOURCE QUALITY SCORING
# ============================================================================

class SourceQualityScorer:
    """Scores source quality based on multiple metrics."""
    
    def __init__(self, registry: SourceRegistry):
        """
        Initialize scorer.
        
        Args:
            registry: SourceRegistry instance
        """
        self.registry = registry
        self.weights = {
            'conversion_rate': 0.4,
            'risk_score': 0.3,
            'consistency': 0.2,
            'cost_efficiency': 0.1
        }
    
    def calculate_quality_score(self, source_name: str) -> Optional[float]:
        """
        Calculate quality score for a source (0-1, higher is better).
        
        Args:
            source_name: Name of the source
            
        Returns:
            Quality score or None if source not found
        """
        profile = self.registry.get_source(source_name)
        if not profile:
            logger.warning(f"Source not found: {source_name}")
            return None
        
        # Conversion score (higher conversion = higher score)
        conversion_score = profile.conversion_rate
        
        # Risk score (lower risk = higher score)
        risk_score = 1 - profile.risk_score
        
        # Consistency score (based on performance history)
        consistency_score = self._calculate_consistency(profile)
        
        # Cost efficiency score
        cost_score = self._calculate_cost_efficiency(profile)
        
        # Weighted average
        quality_score = (
            conversion_score * self.weights['conversion_rate'] +
            risk_score * self.weights['risk_score'] +
            consistency_score * self.weights['consistency'] +
            cost_score * self.weights['cost_efficiency']
        )
        
        return max(0, min(1, quality_score))
    
    def _calculate_consistency(self, profile: SourceProfile) -> float:
        """Calculate consistency score from performance history."""
        if len(profile.performance_history) < 2:
            return 0.5  # Default if no history
        
        conversion_rates = [
            p['actual_conversion_rate']
            for p in profile.performance_history[-10:]  # Last 10 records
        ]
        
        if not conversion_rates:
            return 0.5
        
        avg_rate = sum(conversion_rates) / len(conversion_rates)
        variance = sum((r - avg_rate) ** 2 for r in conversion_rates) / len(conversion_rates)
        std_dev = variance ** 0.5
        
        # Lower standard deviation = higher consistency
        consistency = 1 - min(std_dev, 1.0)
        return consistency
    
    def _calculate_cost_efficiency(self, profile: SourceProfile) -> float:
        """Calculate cost efficiency score."""
        if profile.cost_per_lead == 0:
            return 1.0
        
        # Normalize cost (assuming $100 per lead is "normal")
        normalized_cost = min(profile.cost_per_lead / 100, 1.0)
        return 1 - normalized_cost
    
    def set_weights(self, weights: Dict[str, float]):
        """Set custom weights for scoring."""
        if sum(weights.values()) != 1.0:
            logger.warning("Weights should sum to 1.0")
        self.weights.update(weights)
    
    def rank_sources(self) -> List[Tuple[str, float]]:
        """Get all sources ranked by quality score."""
        scores = []
        for source in self.registry.list_sources():
            score = self.calculate_quality_score(source.source_name)
            if score is not None:
                scores.append((source.source_name, score))
        
        return sorted(scores, key=lambda x: x[1], reverse=True)


# ============================================================================
# 13. AUTOMATIC SOURCE KILL / PAUSE LOGIC
# ============================================================================

class SourceLifecycleManager:
    """Manages source lifecycle (active, paused, killed)."""
    
    def __init__(self, registry: SourceRegistry, scorer: SourceQualityScorer):
        """Initialize manager."""
        self.registry = registry
        self.scorer = scorer
        self.pause_threshold = 0.3
        self.kill_threshold = 0.1
        self.pause_duration_hours = 48
        self.action_log: List[Dict] = []
    
    def evaluate_source_health(self, source_name: str) -> Dict[str, Any]:
        """
        Evaluate source health and recommend action.
        
        Returns:
            Dict with status, score, and recommended action
        """
        score = self.scorer.calculate_quality_score(source_name)
        profile = self.registry.get_source(source_name)
        
        if score is None or profile is None:
            return {
                'source': source_name,
                'status': 'unknown',
                'score': None,
                'action': 'none'
            }
        
        # Determine action
        if score < self.kill_threshold:
            action = 'kill'
            new_status = 'killed'
        elif score < self.pause_threshold:
            action = 'pause'
            new_status = 'paused'
        else:
            action = 'none'
            new_status = 'active'
        
        result = {
            'source': source_name,
            'score': score,
            'status': new_status,
            'action': action,
            'reason': self._get_reason(score, action),
            'timestamp': datetime.now().isoformat()
        }
        
        # Execute action if needed
        if action != 'none':
            self._execute_action(source_name, action, result)
        
        return result
    
    def _get_reason(self, score: float, action: str) -> str:
        """Generate human-readable reason."""
        if action == 'kill':
            return f"Quality score {score:.2f} below kill threshold {self.kill_threshold}"
        elif action == 'pause':
            return f"Quality score {score:.2f} below pause threshold {self.pause_threshold}"
        else:
            return f"Quality score {score:.2f} is acceptable"
    
    def _execute_action(self, source_name: str, action: str, result: Dict):
        """Execute lifecycle action."""
        profile = self.registry.get_source(source_name)
        if not profile:
            return
        
        if action == 'pause':
            profile.is_active = False
            profile.metadata['paused_at'] = datetime.now().isoformat()
            profile.metadata['pause_duration_hours'] = self.pause_duration_hours
            logger.info(f"Source paused: {source_name}")
        
        elif action == 'kill':
            profile.is_active = False
            profile.metadata['killed_at'] = datetime.now().isoformat()
            profile.metadata['kill_reason'] = result['reason']
            logger.error(f"Source killed: {source_name}")
        
        self.action_log.append(result)
    
    def set_thresholds(self, pause: float, kill: float):
        """Set custom thresholds."""
        self.pause_threshold = pause
        self.kill_threshold = kill
    
    def get_action_log(self) -> List[Dict]:
        """Get log of actions taken."""
        return self.action_log


# ============================================================================
# 14. MARKET ZONE PROFILES (City/Region)
# ============================================================================

class MarketZone:
    """Profile for a market zone (city/region)."""
    
    def __init__(
        self,
        zone_name: str,
        average_price: float,
        zone_risk_factor: float,
        inventory_level: float = 0.5,
        demand_factor: float = 0.5,
        metadata: Optional[Dict] = None
    ):
        """
        Initialize market zone.
        
        Args:
            zone_name: Name of zone (city/region)
            average_price: Average property price
            zone_risk_factor: Risk factor (0-1, higher = more risky)
            inventory_level: Inventory level (0-1)
            demand_factor: Demand factor (0-1)
            metadata: Additional metadata
        """
        self.zone_name = zone_name
        self.average_price = average_price
        self.zone_risk_factor = max(0, min(1, zone_risk_factor))
        self.inventory_level = max(0, min(1, inventory_level))
        self.demand_factor = max(0, min(1, demand_factor))
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        logger.info(
            f"Market zone created: {zone_name} "
            f"(price=${average_price:,.0f}, risk={zone_risk_factor})"
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'zone_name': self.zone_name,
            'average_price': self.average_price,
            'zone_risk_factor': self.zone_risk_factor,
            'inventory_level': self.inventory_level,
            'demand_factor': self.demand_factor,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MarketRegistry:
    """Registry for market zones."""
    
    def __init__(self):
        """Initialize market registry."""
        self.zones: Dict[str, MarketZone] = {}
    
    def add_zone(
        self,
        zone_name: str,
        average_price: float,
        zone_risk_factor: float,
        **kwargs
    ) -> MarketZone:
        """Add market zone."""
        zone = MarketZone(zone_name, average_price, zone_risk_factor, **kwargs)
        self.zones[zone_name] = zone
        return zone
    
    def get_zone(self, zone_name: str) -> Optional[MarketZone]:
        """Get market zone."""
        return self.zones.get(zone_name)
    
    def update_zone(self, zone_name: str, **kwargs):
        """Update market zone."""
        zone = self.zones.get(zone_name)
        if zone:
            for key, value in kwargs.items():
                if hasattr(zone, key) and not key.startswith('_'):
                    setattr(zone, key, value)
            zone.updated_at = datetime.now()
        return zone


# ============================================================================
# 15. AUTO-ADJUSTED CAPS PER ZONE
# ============================================================================

class DealCapCalculator:
    """Calculates deal caps based on market zones."""
    
    def __init__(self, market_registry: MarketRegistry):
        """Initialize calculator."""
        self.market_registry = market_registry
        self.cap_adjustments: Dict[str, float] = {}
    
    def calculate_deal_cap(self, zone_name: str, method: str = 'basic') -> Optional[float]:
        """
        Calculate deal cap for a zone.
        
        Args:
            zone_name: Name of market zone
            method: Calculation method ('basic', 'demand_adjusted', 'inventory_adjusted')
            
        Returns:
            Deal cap or None if zone not found
        """
        zone = self.market_registry.get_zone(zone_name)
        if not zone:
            logger.warning(f"Zone not found: {zone_name}")
            return None
        
        if method == 'basic':
            cap = zone.average_price * (1 - zone.zone_risk_factor)
        
        elif method == 'demand_adjusted':
            # Higher demand = higher cap
            demand_multiplier = 0.8 + (zone.demand_factor * 0.4)
            cap = zone.average_price * (1 - zone.zone_risk_factor) * demand_multiplier
        
        elif method == 'inventory_adjusted':
            # Lower inventory = lower cap (less deals available)
            inventory_multiplier = 0.7 + (zone.inventory_level * 0.3)
            cap = zone.average_price * (1 - zone.zone_risk_factor) * inventory_multiplier
        
        else:
            cap = zone.average_price * (1 - zone.zone_risk_factor)
        
        self.cap_adjustments[zone_name] = cap
        return cap
    
    def get_all_caps(self, method: str = 'basic') -> Dict[str, float]:
        """Get caps for all zones."""
        caps = {}
        for zone in self.market_registry.zones.values():
            cap = self.calculate_deal_cap(zone.zone_name, method)
            if cap is not None:
                caps[zone.zone_name] = cap
        return caps


# ============================================================================
# 16. DUPLICATE & IDENTITY RESOLUTION
# ============================================================================

class DuplicateResolver:
    """Resolves duplicate leads and consolidates identities."""
    
    def __init__(self):
        """Initialize resolver."""
        self.identity_map: Dict[str, str] = {}  # Maps various identifiers to canonical ID
        self.resolution_log: List[Dict] = []
    
    def resolve_duplicates(
        self,
        leads: List[Dict],
        identity_field: str = 'email'
    ) -> List[Dict]:
        """
        Resolve duplicates in lead list.
        
        Args:
            leads: List of lead dictionaries
            identity_field: Field to use for deduplication
            
        Returns:
            List of unique leads
        """
        unique_leads = {}
        duplicates = []
        
        for lead in leads:
            identity = lead.get(identity_field)
            
            if identity is None:
                # No identity field, include anyway
                unique_leads[id(lead)] = lead
                continue
            
            if identity not in unique_leads:
                unique_leads[identity] = lead
                self.identity_map[identity] = identity
            else:
                # Duplicate found
                duplicates.append({
                    'timestamp': datetime.now().isoformat(),
                    'identity_field': identity_field,
                    'identity': identity,
                    'canonical_lead': unique_leads[identity].get('name'),
                    'duplicate_lead': lead.get('name')
                })
                
                # Keep lead with more complete data
                unique_leads[identity] = self._merge_leads(
                    unique_leads[identity],
                    lead
                )
        
        if duplicates:
            self.resolution_log.extend(duplicates)
            logger.info(f"Resolved {len(duplicates)} duplicates")
        
        return list(unique_leads.values())
    
    def _merge_leads(self, lead1: Dict, lead2: Dict) -> Dict:
        """Merge two lead records, preferring non-null values."""
        merged = lead1.copy()
        for key, value in lead2.items():
            if value is not None and merged.get(key) is None:
                merged[key] = value
        return merged
    
    def add_identity_alias(self, alias: str, canonical_id: str):
        """Map identity alias to canonical ID."""
        self.identity_map[alias] = canonical_id
    
    def get_canonical_id(self, identifier: str) -> str:
        """Get canonical ID for an identifier."""
        return self.identity_map.get(identifier, identifier)


# ============================================================================
# 17. STUCK-STAGE ESCALATION ENGINE
# ============================================================================

class StageEscalationEngine:
    """Detects and escalates leads stuck in stages."""
    
    def __init__(self):
        """Initialize escalation engine."""
        self.escalation_thresholds: Dict[str, int] = {
            'lead': 7,      # 7 days
            'contact': 5,   # 5 days
            'negotiation': 14,  # 14 days
            'closing': 10,  # 10 days
        }
        self.escalation_log: List[Dict] = []
    
    def evaluate_lead_progression(self, lead: Dict) -> Dict[str, Any]:
        """
        Evaluate if lead is stuck and needs escalation.
        
        Args:
            lead: Lead data with stage and stage_duration
            
        Returns:
            Escalation status and recommendation
        """
        stage = lead.get('stage', 'unknown')
        stage_duration = lead.get('stage_duration_days', 0)
        lead_id = lead.get('id', lead.get('name', 'unknown'))
        
        threshold = self.escalation_thresholds.get(stage, 7)
        
        if stage_duration > threshold:
            reason = (
                f"Lead stuck in '{stage}' stage for {stage_duration} days "
                f"(threshold: {threshold} days)"
            )
            escalation = {
                'lead_id': lead_id,
                'stage': stage,
                'stage_duration_days': stage_duration,
                'threshold_days': threshold,
                'is_escalated': True,
                'reason': reason,
                'priority': self._calculate_priority(stage_duration, threshold),
                'timestamp': datetime.now().isoformat()
            }
        else:
            escalation = {
                'lead_id': lead_id,
                'stage': stage,
                'stage_duration_days': stage_duration,
                'threshold_days': threshold,
                'is_escalated': False,
                'reason': f"Lead progressing normally (due: {threshold - stage_duration} days)",
                'priority': 'normal',
                'timestamp': datetime.now().isoformat()
            }
        
        if escalation['is_escalated']:
            self.escalation_log.append(escalation)
        
        return escalation
    
    def _calculate_priority(self, duration: int, threshold: int) -> str:
        """Calculate priority based on overdue duration."""
        overdue_percentage = (duration - threshold) / threshold
        if overdue_percentage > 2:
            return 'critical'
        elif overdue_percentage > 1:
            return 'high'
        else:
            return 'medium'
    
    def set_threshold(self, stage: str, days: int):
        """Set escalation threshold for stage."""
        self.escalation_thresholds[stage] = days
    
    def get_escalated_leads(self) -> List[Dict]:
        """Get all escalated leads."""
        return [e for e in self.escalation_log if e['is_escalated']]


# ============================================================================
# 18. CONE PRIORITIZATION TUNING (Top-10 / Big Game)
# ============================================================================

class ConePrioritizer:
    """Prioritizes leads using cone methodology."""
    
    def __init__(self):
        """Initialize prioritizer."""
        self.priority_factors = {
            'deal_size': 0.35,
            'conversion_likelihood': 0.35,
            'timeline': 0.2,
            'relationship_strength': 0.1
        }
        self.priority_log: List[Dict] = []
    
    def prioritize_leads(
        self,
        leads: List[Dict],
        top_n: int = 10
    ) -> List[Dict]:
        """
        Prioritize leads using cone methodology.
        
        Args:
            leads: List of leads
            top_n: Number of top leads to return
            
        Returns:
            Top-N prioritized leads
        """
        scored_leads = []
        
        for lead in leads:
            score = self._calculate_priority_score(lead)
            scored_leads.append({
                'lead': lead,
                'score': score,
                'timestamp': datetime.now().isoformat()
            })
        
        # Sort by score descending
        scored_leads.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top-N
        top_leads = scored_leads[:top_n]
        
        # Log prioritization
        for item in top_leads:
            self.priority_log.append({
                'lead_id': item['lead'].get('id'),
                'rank': len(self.priority_log) + 1,
                'score': item['score'],
                'timestamp': item['timestamp']
            })
        
        return [item['lead'] for item in top_leads]
    
    def _calculate_priority_score(self, lead: Dict) -> float:
        """Calculate priority score for lead."""
        deal_size_score = lead.get('deal_size_score', 0.5)
        conversion_score = lead.get('conversion_likelihood', 0.5)
        timeline_score = lead.get('timeline_score', 0.5)
        relationship_score = lead.get('relationship_strength', 0.5)
        
        score = (
            deal_size_score * self.priority_factors['deal_size'] +
            conversion_score * self.priority_factors['conversion_likelihood'] +
            timeline_score * self.priority_factors['timeline'] +
            relationship_score * self.priority_factors['relationship_strength']
        )
        
        return max(0, min(1, score))
    
    def set_factors(self, factors: Dict[str, float]):
        """Set custom priority factors."""
        if sum(factors.values()) != 1.0:
            logger.warning("Factors should sum to 1.0")
        self.priority_factors.update(factors)


# ============================================================================
# 19. SHIELD TELEMETRY THRESHOLDS
# ============================================================================

class ShieldMonitor:
    """Monitors shield thresholds and alerts on breaches."""
    
    class ShieldAlert(Enum):
        SAFE = "safe"
        WARNING = "warning"
        CRITICAL = "critical"
    
    def __init__(self):
        """Initialize shield monitor."""
        self.shields: Dict[str, Dict] = {}
        self.alert_log: List[Dict] = []
        self.subscribers: Dict[str, List] = {}
    
    def register_shield(
        self,
        shield_name: str,
        warning_threshold: float,
        critical_threshold: float,
        current_value: float = 0.0,
        unit: str = ""
    ):
        """Register a shield for monitoring."""
        self.shields[shield_name] = {
            'name': shield_name,
            'warning_threshold': warning_threshold,
            'critical_threshold': critical_threshold,
            'current_value': current_value,
            'unit': unit,
            'last_checked': datetime.now().isoformat(),
            'history': []
        }
        self.subscribers[shield_name] = []
        logger.info(f"Shield registered: {shield_name}")
    
    def update_shield_value(self, shield_name: str, value: float) -> 'ShieldMonitor.ShieldAlert':
        """
        Update shield value and check thresholds.
        
        Returns:
            Alert level
        """
        shield = self.shields.get(shield_name)
        if not shield:
            logger.warning(f"Shield not found: {shield_name}")
            return self.ShieldAlert.SAFE
        
        shield['current_value'] = value
        shield['last_checked'] = datetime.now().isoformat()
        shield['history'].append({
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        
        # Determine alert level
        if value >= shield['critical_threshold']:
            alert_level = self.ShieldAlert.CRITICAL
        elif value >= shield['warning_threshold']:
            alert_level = self.ShieldAlert.WARNING
        else:
            alert_level = self.ShieldAlert.SAFE
        
        # Log if not safe
        if alert_level != self.ShieldAlert.SAFE:
            self._log_alert(shield_name, alert_level, value, shield)
            self._notify_subscribers(shield_name, alert_level, value)
        
        return alert_level
    
    def _log_alert(self, shield_name: str, alert_level: 'ShieldMonitor.ShieldAlert', value: float, shield: Dict):
        """Log shield alert."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'shield_name': shield_name,
            'alert_level': alert_level.value,
            'value': value,
            'unit': shield['unit'],
            'warning_threshold': shield['warning_threshold'],
            'critical_threshold': shield['critical_threshold']
        }
        self.alert_log.append(alert)
        
        log_func = logger.warning if alert_level == self.ShieldAlert.WARNING else logger.error
        log_func(
            f"Shield {shield_name} {alert_level.value}: "
            f"{value}{shield['unit']} "
            f"(warning: {shield['warning_threshold']}, critical: {shield['critical_threshold']})"
        )
    
    def subscribe(self, shield_name: str, callback):
        """Subscribe to shield alerts."""
        if shield_name in self.subscribers:
            self.subscribers[shield_name].append(callback)
    
    def _notify_subscribers(self, shield_name: str, alert_level: 'ShieldMonitor.ShieldAlert', value: float):
        """Notify subscribers of alert."""
        for callback in self.subscribers.get(shield_name, []):
            try:
                callback({
                    'shield_name': shield_name,
                    'alert_level': alert_level.value,
                    'value': value
                })
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")


# ============================================================================
# 20. DECISION REASONING LOG ("Why This Happened")
# ============================================================================

class DecisionLogger:
    """Logs decision reasoning for all key actions."""
    
    class DecisionCategory(Enum):
        LEAD_SCORING = "lead_scoring"
        LEAD_ASSIGNMENT = "lead_assignment"
        DEAL_APPROVAL = "deal_approval"
        SOURCE_MANAGEMENT = "source_management"
        MARKET_ANALYSIS = "market_analysis"
        ESCALATION = "escalation"
        PRIORITIZATION = "prioritization"
        OTHER = "other"
    
    def __init__(self):
        """Initialize decision logger."""
        self.decisions: List[Dict] = []
    
    def log_decision(
        self,
        decision_type: str,
        category: DecisionCategory,
        reason: str,
        metadata: Optional[Dict] = None,
        confidence: float = 0.5
    ) -> str:
        """
        Log a decision with reasoning.
        
        Args:
            decision_type: Type of decision
            category: Decision category
            reason: Explanation of why decision was made
            metadata: Additional context
            confidence: Confidence level (0-1)
            
        Returns:
            Decision ID
        """
        decision_id = f"dec_{len(self.decisions)}_{int(datetime.now().timestamp())}"
        
        decision = {
            'id': decision_id,
            'type': decision_type,
            'category': category.value,
            'reason': reason,
            'confidence': max(0, min(1, confidence)),
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'context_snapshot': self._get_context_snapshot()
        }
        
        self.decisions.append(decision)
        
        logger.info(
            f"Decision logged: {decision_type} "
            f"(category={category.value}, confidence={confidence:.2f}) - {reason}"
        )
        
        return decision_id
    
    def _get_context_snapshot(self) -> Dict:
        """Get system context snapshot."""
        return {
            'timestamp': datetime.now().isoformat(),
            'decisions_logged': len(self.decisions)
        }
    
    def get_decision(self, decision_id: str) -> Optional[Dict]:
        """Get decision by ID."""
        for decision in self.decisions:
            if decision['id'] == decision_id:
                return decision
        return None
    
    def get_decisions_by_type(self, decision_type: str) -> List[Dict]:
        """Get all decisions of a specific type."""
        return [d for d in self.decisions if d['type'] == decision_type]
    
    def get_decisions_by_category(self, category: DecisionCategory) -> List[Dict]:
        """Get all decisions in a category."""
        return [d for d in self.decisions if d['category'] == category.value]
    
    def get_audit_trail(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict]:
        """Get decisions within time range."""
        results = []
        for decision in self.decisions:
            decision_time = datetime.fromisoformat(decision['timestamp'])
            if start_time and decision_time < start_time:
                continue
            if end_time and decision_time > end_time:
                continue
            results.append(decision)
        return results
    
    def export_decisions(self, format: str = 'json') -> str:
        """Export decisions in specified format."""
        if format == 'json':
            return json.dumps(self.decisions, indent=2)
        else:
            return str(self.decisions)


# ============================================================================
# BRAIN INTELLIGENCE ORCHESTRATOR
# ============================================================================

class BrainIntelligenceOrchestrator:
    """Orchestrates all Batch 2 components."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.source_registry = SourceRegistry()
        self.source_scorer = SourceQualityScorer(self.source_registry)
        self.source_lifecycle = SourceLifecycleManager(self.source_registry, self.source_scorer)
        self.market_registry = MarketRegistry()
        self.deal_cap_calculator = DealCapCalculator(self.market_registry)
        self.duplicate_resolver = DuplicateResolver()
        self.escalation_engine = StageEscalationEngine()
        self.cone_prioritizer = ConePrioritizer()
        self.shield_monitor = ShieldMonitor()
        self.decision_logger = DecisionLogger()
        
        logger.info("BrainIntelligenceOrchestrator initialized")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            'sources_count': len(self.source_registry.sources),
            'active_sources': len(self.source_registry.get_active_sources()),
            'zones_count': len(self.market_registry.zones),
            'decisions_logged': len(self.decision_logger.decisions),
            'escalated_leads': len(self.escalation_engine.get_escalated_leads()),
            'alerts': len(self.shield_monitor.alert_log)
        }
    
    def analyze_deal(self, deal: Dict) -> Dict[str, Any]:
        """Comprehensive deal analysis."""
        analysis = {
            'deal_id': deal.get('id'),
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Source analysis
        source_name = deal.get('source')
        if source_name:
            source_score = self.source_scorer.calculate_quality_score(source_name)
            analysis['components']['source'] = {
                'name': source_name,
                'quality_score': source_score
            }
        
        # Zone analysis
        zone_name = deal.get('zone')
        if zone_name:
            deal_cap = self.deal_cap_calculator.calculate_deal_cap(zone_name)
            analysis['components']['zone'] = {
                'name': zone_name,
                'deal_cap': deal_cap
            }
        
        # Prioritization
        priority = self.cone_prioritizer._calculate_priority_score(deal)
        analysis['components']['priority'] = {
            'score': priority,
            'rank': 'high' if priority > 0.7 else 'medium' if priority > 0.4 else 'low'
        }
        
        return analysis


# Module initialization
def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
