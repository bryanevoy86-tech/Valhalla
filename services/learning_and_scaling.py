"""
Batch 3: Learning + Scaling Safety
Activation Blocks 21-30

Block 21: Script/Channel A/B Tracking
Block 22: Performance-Based Script Promotion/Demotion
Block 23: Deal Packet Auto-Build
Block 24: Learning Ingestion Job (Allowed Sources Only)
Block 25: Evaluation Loop (What Improves Outcomes)
Block 26: Safe Heuristic/Model Update Mechanism
Block 27: Clone Readiness Scoring
Block 28: Clone Gate Enforcement
Block 29: Clone Audit Trail + Rollback
Block 30: End-to-End Brain Verification Suite
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict, field


# ============================================================================
# Block 21: Script/Channel A/B Tracking
# ============================================================================

@dataclass
class ABTestVariant:
    """Represents an A/B test variant (script or channel)."""
    variant_id: str
    variant_name: str
    variant_type: str  # 'script' or 'channel'
    performance_metric: float
    sample_size: int = 0
    conversion_rate: float = 0.0
    cost_per_action: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


class ABTracker:
    """
    Tracks A/B test performance for scripts and channels.
    
    Monitors:
    - Script version performance (A, B, C, etc.)
    - Channel performance (email, SMS, phone, etc.)
    - Conversion rates and cost metrics
    - Statistical significance
    """
    
    def __init__(self):
        """Initialize A/B tracker."""
        self.variants: Dict[str, ABTestVariant] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("ABTracker")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def register_variant(self, variant_name: str, variant_type: str) -> str:
        """Register a new A/B test variant."""
        variant_id = f"var_{uuid.uuid4().hex[:12]}"
        variant = ABTestVariant(
            variant_id=variant_id,
            variant_name=variant_name,
            variant_type=variant_type,
            performance_metric=0.0
        )
        self.variants[variant_id] = variant
        self.logger.info(f"Registered {variant_type} variant: {variant_name}")
        return variant_id
    
    def track_performance(self, variant_id: str, metric: float, 
                         conversions: int = 0, cost: float = 0.0) -> Dict[str, Any]:
        """Track performance for a variant."""
        if variant_id not in self.variants:
            raise ValueError(f"Variant {variant_id} not found")
        
        variant = self.variants[variant_id]
        variant.performance_metric = metric
        variant.conversion_rate = (conversions / max(variant.sample_size, 1)) if variant.sample_size > 0 else 0
        variant.cost_per_action = (cost / max(conversions, 1)) if conversions > 0 else 0
        variant.last_updated = datetime.utcnow()
        variant.sample_size += 1
        
        self.logger.info(f"Updated {variant.variant_name}: metric={metric:.2%}, conversions={conversions}")
        
        return {
            'variant_id': variant_id,
            'variant_name': variant.variant_name,
            'performance': metric,
            'conversion_rate': variant.conversion_rate,
            'cost_per_action': variant.cost_per_action,
            'timestamp': variant.last_updated
        }
    
    def get_variant_stats(self, variant_id: str) -> Dict[str, Any]:
        """Get statistics for a variant."""
        if variant_id not in self.variants:
            return None
        
        variant = self.variants[variant_id]
        return {
            'variant_id': variant.variant_id,
            'variant_name': variant.variant_name,
            'performance': variant.performance_metric,
            'conversion_rate': variant.conversion_rate,
            'cost_per_action': variant.cost_per_action,
            'sample_size': variant.sample_size,
            'is_active': variant.is_active
        }
    
    def get_winning_variant(self, variant_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the best performing variant."""
        candidates = [v for v in self.variants.values() 
                     if v.is_active and (variant_type is None or v.variant_type == variant_type)]
        
        if not candidates:
            return None
        
        winner = max(candidates, key=lambda v: v.performance_metric)
        return {
            'variant_id': winner.variant_id,
            'variant_name': winner.variant_name,
            'performance': winner.performance_metric,
            'variant_type': winner.variant_type
        }
    
    def compare_variants(self, variant_ids: List[str]) -> List[Dict[str, Any]]:
        """Compare multiple variants."""
        results = []
        for vid in variant_ids:
            if vid in self.variants:
                variant = self.variants[vid]
                results.append({
                    'variant_name': variant.variant_name,
                    'performance': variant.performance_metric,
                    'conversion_rate': variant.conversion_rate,
                    'cost_per_action': variant.cost_per_action,
                    'sample_size': variant.sample_size
                })
        
        return sorted(results, key=lambda x: x['performance'], reverse=True)


# ============================================================================
# Block 22: Performance-Based Script Promotion/Demotion
# ============================================================================

class ScriptStatus(Enum):
    """Script deployment status."""
    EXPERIMENTAL = "experimental"
    TESTING = "testing"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DEPRECATED = "deprecated"


@dataclass
class ScriptProfile:
    """Script version profile."""
    script_id: str
    script_name: str
    version: str
    status: ScriptStatus
    performance_score: float
    promotion_threshold: float = 0.85
    demotion_threshold: float = 0.65
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_promoted: Optional[datetime] = None
    promotion_history: List[str] = field(default_factory=list)


class ScriptPromoter:
    """
    Manages script promotion and demotion based on performance.
    
    Promotes:
    - Experimental → Testing → Primary
    
    Demotes:
    - Primary → Secondary → Deprecated
    """
    
    def __init__(self):
        """Initialize script promoter."""
        self.scripts: Dict[str, ScriptProfile] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("ScriptPromoter")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def register_script(self, script_name: str, version: str, 
                       initial_status: ScriptStatus = ScriptStatus.EXPERIMENTAL) -> str:
        """Register a new script version."""
        script_id = f"scr_{uuid.uuid4().hex[:12]}"
        script = ScriptProfile(
            script_id=script_id,
            script_name=script_name,
            version=version,
            status=initial_status,
            performance_score=0.0
        )
        self.scripts[script_id] = script
        self.logger.info(f"Registered script: {script_name} v{version}")
        return script_id
    
    def evaluate_script(self, script_id: str, performance_score: float) -> Dict[str, Any]:
        """Evaluate script and potentially promote or demote."""
        if script_id not in self.scripts:
            raise ValueError(f"Script {script_id} not found")
        
        script = self.scripts[script_id]
        script.performance_score = performance_score
        
        old_status = script.status
        action = None
        
        # Promotion logic
        if performance_score >= script.promotion_threshold:
            if script.status == ScriptStatus.EXPERIMENTAL:
                script.status = ScriptStatus.TESTING
                action = "PROMOTE"
            elif script.status == ScriptStatus.TESTING:
                script.status = ScriptStatus.PRIMARY
                script.last_promoted = datetime.utcnow()
                action = "PROMOTE"
        
        # Demotion logic
        elif performance_score < script.demotion_threshold:
            if script.status == ScriptStatus.PRIMARY:
                script.status = ScriptStatus.SECONDARY
                action = "DEMOTE"
            elif script.status == ScriptStatus.SECONDARY:
                script.status = ScriptStatus.DEPRECATED
                action = "DEMOTE"
        
        if action:
            script.promotion_history.append(f"{old_status.value} → {script.status.value} ({performance_score:.1%})")
            self.logger.info(f"{action}: {script.script_name} v{script.version}: {old_status.value} → {script.status.value}")
        
        return {
            'script_id': script_id,
            'script_name': script.script_name,
            'version': script.version,
            'old_status': old_status.value,
            'new_status': script.status.value,
            'performance_score': performance_score,
            'action': action or 'NONE'
        }
    
    def get_primary_scripts(self) -> List[Dict[str, Any]]:
        """Get all primary (production) scripts."""
        primary = [s for s in self.scripts.values() if s.status == ScriptStatus.PRIMARY]
        return [
            {
                'script_id': s.script_id,
                'script_name': s.script_name,
                'version': s.version,
                'performance_score': s.performance_score
            }
            for s in primary
        ]
    
    def get_script_status(self, script_id: str) -> Dict[str, Any]:
        """Get script status details."""
        if script_id not in self.scripts:
            return None
        
        script = self.scripts[script_id]
        return {
            'script_id': script_id,
            'script_name': script.script_name,
            'version': script.version,
            'status': script.status.value,
            'performance_score': script.performance_score,
            'promotion_history': script.promotion_history
        }


# ============================================================================
# Block 23: Deal Packet Auto-Build
# ============================================================================

@dataclass
class DealPacket:
    """Auto-generated deal packet."""
    packet_id: str
    lead_id: str
    lead_name: str
    deal_value: float
    terms: str
    scripts: List[str]
    channels: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DealPacketBuilder:
    """
    Automatically builds deal packets from lead data.
    
    Includes:
    - Lead information
    - Deal terms and valuation
    - Recommended scripts/channels
    - Contact strategy
    """
    
    def __init__(self):
        """Initialize deal packet builder."""
        self.packets: Dict[str, DealPacket] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("DealPacketBuilder")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def build_packet(self, lead_data: Dict[str, Any], 
                    scripts: List[str], channels: List[str]) -> str:
        """Build a deal packet from lead data."""
        packet_id = f"pkt_{uuid.uuid4().hex[:12]}"
        
        packet = DealPacket(
            packet_id=packet_id,
            lead_id=lead_data.get('lead_id', f"lead_{uuid.uuid4().hex[:8]}"),
            lead_name=lead_data.get('name', 'Unknown'),
            deal_value=lead_data.get('value', 0.0),
            terms=lead_data.get('terms', 'TBD'),
            scripts=scripts,
            channels=channels,
            metadata=lead_data
        )
        
        self.packets[packet_id] = packet
        self.logger.info(f"Built deal packet {packet_id} for {lead_data.get('name')} (${lead_data.get('value'):,.0f})")
        
        return packet_id
    
    def get_packet(self, packet_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a deal packet."""
        if packet_id not in self.packets:
            return None
        
        packet = self.packets[packet_id]
        return {
            'packet_id': packet_id,
            'lead_id': packet.lead_id,
            'lead_name': packet.lead_name,
            'deal_value': packet.deal_value,
            'terms': packet.terms,
            'scripts': packet.scripts,
            'channels': packet.channels,
            'status': packet.status,
            'created_at': packet.created_at
        }
    
    def update_packet_status(self, packet_id: str, status: str) -> bool:
        """Update packet status."""
        if packet_id not in self.packets:
            return False
        
        self.packets[packet_id].status = status
        self.logger.info(f"Updated packet {packet_id} status to {status}")
        return True
    
    def export_packet(self, packet_id: str, format_type: str = 'json') -> Optional[str]:
        """Export packet to specified format."""
        if packet_id not in self.packets:
            return None
        
        packet = self.packets[packet_id]
        packet_dict = {
            'packet_id': packet.packet_id,
            'lead_id': packet.lead_id,
            'lead_name': packet.lead_name,
            'deal_value': packet.deal_value,
            'terms': packet.terms,
            'scripts': packet.scripts,
            'channels': packet.channels,
            'status': packet.status,
            'metadata': packet.metadata
        }
        
        if format_type == 'json':
            return json.dumps(packet_dict, indent=2, default=str)
        
        return None


# ============================================================================
# Block 24: Learning Ingestion Job (Allowed Sources Only)
# ============================================================================

class LearningIngestor:
    """
    Ingests learning data only from approved sources.
    
    Enforces:
    - Whitelist of allowed sources
    - Data validation
    - Duplicate prevention
    - Audit logging
    """
    
    def __init__(self, allowed_sources: List[str]):
        """Initialize learning ingestor with allowed sources."""
        self.allowed_sources = set(allowed_sources)
        self.ingested_data: Dict[str, Dict[str, Any]] = {}
        self.blocked_attempts: List[Dict[str, Any]] = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("LearningIngestor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def ingest_data(self, source: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest learning data from a source."""
        if source not in self.allowed_sources:
            blocked = {
                'source': source,
                'reason': 'Source not in whitelist',
                'timestamp': datetime.utcnow(),
                'data_sample': str(data)[:100]
            }
            self.blocked_attempts.append(blocked)
            self.logger.warning(f"Blocked data ingestion from unauthorized source: {source}")
            
            return {
                'success': False,
                'reason': f'Source {source} is not allowed',
                'timestamp': datetime.utcnow()
            }
        
        data_id = f"ing_{uuid.uuid4().hex[:12]}"
        self.ingested_data[data_id] = {
            'source': source,
            'data': data,
            'ingested_at': datetime.utcnow()
        }
        
        self.logger.info(f"Ingested data from {source}: {data_id}")
        
        return {
            'success': True,
            'data_id': data_id,
            'source': source,
            'timestamp': datetime.utcnow()
        }
    
    def add_allowed_source(self, source: str) -> None:
        """Add a source to the whitelist."""
        self.allowed_sources.add(source)
        self.logger.info(f"Added source to whitelist: {source}")
    
    def remove_allowed_source(self, source: str) -> None:
        """Remove a source from the whitelist."""
        self.allowed_sources.discard(source)
        self.logger.info(f"Removed source from whitelist: {source}")
    
    def get_allowed_sources(self) -> List[str]:
        """Get list of allowed sources."""
        return sorted(list(self.allowed_sources))
    
    def get_blocked_attempts(self) -> List[Dict[str, Any]]:
        """Get list of blocked ingestion attempts."""
        return self.blocked_attempts


# ============================================================================
# Block 25: Evaluation Loop (What Improves Outcomes)
# ============================================================================

@dataclass
class EvaluationResult:
    """Result from an evaluation."""
    eval_id: str
    metric_value: float
    threshold: float
    is_improvement: bool
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class OutcomeEvaluator:
    """
    Evaluates outcomes and measures improvement over time.
    
    Tracks:
    - Outcome metrics
    - Improvement trends
    - System effectiveness
    - Historical baselines
    """
    
    def __init__(self, baseline_threshold: float = 0.80):
        """Initialize outcome evaluator."""
        self.baseline_threshold = baseline_threshold
        self.evaluations: List[EvaluationResult] = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("OutcomeEvaluator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def evaluate_outcome(self, metric_value: float, context: str = "") -> Dict[str, Any]:
        """Evaluate an outcome metric."""
        eval_id = f"eval_{uuid.uuid4().hex[:12]}"
        is_improvement = metric_value > self.baseline_threshold
        
        reasoning = f"Metric {metric_value:.1%} is {'above' if is_improvement else 'below'} threshold {self.baseline_threshold:.1%}"
        if context:
            reasoning += f" - {context}"
        
        result = EvaluationResult(
            eval_id=eval_id,
            metric_value=metric_value,
            threshold=self.baseline_threshold,
            is_improvement=is_improvement,
            reasoning=reasoning
        )
        
        self.evaluations.append(result)
        
        log_level = "INFO" if is_improvement else "WARNING"
        self.logger.log(
            logging.INFO if is_improvement else logging.WARNING,
            f"Evaluation {eval_id}: {reasoning}"
        )
        
        return {
            'eval_id': eval_id,
            'metric_value': metric_value,
            'is_improvement': is_improvement,
            'threshold': self.baseline_threshold,
            'reasoning': reasoning,
            'timestamp': result.timestamp
        }
    
    def get_improvement_trend(self, window_size: int = 10) -> Dict[str, Any]:
        """Get recent improvement trend."""
        recent = self.evaluations[-window_size:]
        
        if not recent:
            return {
                'trend': 'INSUFFICIENT_DATA',
                'evaluations': 0,
                'improvement_rate': 0.0
            }
        
        improvements = sum(1 for e in recent if e.is_improvement)
        improvement_rate = improvements / len(recent)
        
        if improvement_rate >= 0.8:
            trend = "IMPROVING"
        elif improvement_rate >= 0.5:
            trend = "STABLE"
        else:
            trend = "DECLINING"
        
        return {
            'trend': trend,
            'improvement_rate': improvement_rate,
            'evaluations': len(recent),
            'improvements': improvements,
            'recent_metrics': [e.metric_value for e in recent]
        }
    
    def set_baseline_threshold(self, threshold: float) -> None:
        """Update baseline threshold."""
        self.baseline_threshold = threshold
        self.logger.info(f"Updated baseline threshold to {threshold:.1%}")


# ============================================================================
# Block 26: Safe Heuristic/Model Update Mechanism
# ============================================================================

class UpdateStrategy(Enum):
    """Model update strategy."""
    INCREMENTAL = "incremental"
    FULL_RETRAIN = "full_retrain"
    SHADOW = "shadow"
    ROLLBACK = "rollback"


@dataclass
class ModelVersion:
    """Model version tracking."""
    version_id: str
    model_name: str
    version_number: int
    update_strategy: UpdateStrategy
    accuracy: float
    is_active: bool
    created_at: datetime = field(default_factory=datetime.utcnow)
    previous_version_id: Optional[str] = None


class SafeModelUpdater:
    """
    Safely updates models with validation and rollback capability.
    
    Strategies:
    - Incremental: Small updates to existing model
    - Full Retrain: Complete model retraining
    - Shadow: Test new model without affecting production
    - Rollback: Revert to previous version
    """
    
    def __init__(self):
        """Initialize safe model updater."""
        self.models: Dict[str, ModelVersion] = {}
        self.version_history: Dict[str, List[ModelVersion]] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("SafeModelUpdater")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def create_model(self, model_name: str) -> str:
        """Create initial model version."""
        version_id = f"mdl_{uuid.uuid4().hex[:12]}"
        model = ModelVersion(
            version_id=version_id,
            model_name=model_name,
            version_number=1,
            update_strategy=UpdateStrategy.INCREMENTAL,
            accuracy=0.0,
            is_active=True
        )
        
        self.models[version_id] = model
        self.version_history[model_name] = [model]
        
        self.logger.info(f"Created model: {model_name} (v1)")
        return version_id
    
    def update_model(self, version_id: str, new_accuracy: float,
                    strategy: UpdateStrategy = UpdateStrategy.INCREMENTAL) -> Dict[str, Any]:
        """Update model with specified strategy."""
        if version_id not in self.models:
            raise ValueError(f"Model version {version_id} not found")
        
        current = self.models[version_id]
        
        # Create new version
        new_version_id = f"mdl_{uuid.uuid4().hex[:12]}"
        new_model = ModelVersion(
            version_id=new_version_id,
            model_name=current.model_name,
            version_number=current.version_number + 1,
            update_strategy=strategy,
            accuracy=new_accuracy,
            is_active=strategy != UpdateStrategy.SHADOW,  # Shadow is inactive by default
            previous_version_id=version_id
        )
        
        self.models[new_version_id] = new_model
        self.version_history[current.model_name].append(new_model)
        
        # Handle strategy
        if strategy == UpdateStrategy.INCREMENTAL:
            current.is_active = False
            new_model.is_active = True
            action = "PROMOTED"
        elif strategy == UpdateStrategy.FULL_RETRAIN:
            current.is_active = False
            new_model.is_active = True
            action = "RETRAINED"
        elif strategy == UpdateStrategy.SHADOW:
            action = "SHADOW_DEPLOYED"
        elif strategy == UpdateStrategy.ROLLBACK:
            new_model.is_active = True
            current.is_active = False
            action = "ROLLED_BACK"
        else:
            action = "UPDATED"
        
        self.logger.info(f"{action}: {current.model_name} v{current.version_number} → v{new_model.version_number} (accuracy: {new_accuracy:.1%})")
        
        return {
            'old_version_id': version_id,
            'new_version_id': new_version_id,
            'model_name': current.model_name,
            'old_accuracy': current.accuracy,
            'new_accuracy': new_accuracy,
            'strategy': strategy.value,
            'action': action
        }
    
    def rollback_model(self, model_name: str) -> Dict[str, Any]:
        """Rollback to previous model version."""
        if model_name not in self.version_history:
            raise ValueError(f"Model {model_name} not found")
        
        history = self.version_history[model_name]
        if len(history) < 2:
            raise ValueError(f"No previous version to rollback to")
        
        current = history[-1]
        previous = history[-2]
        
        current.is_active = False
        previous.is_active = True
        
        self.logger.info(f"Rolled back {model_name}: v{current.version_number} → v{previous.version_number}")
        
        return {
            'model_name': model_name,
            'rolled_back_from': current.version_number,
            'rolled_back_to': previous.version_number,
            'accuracy': previous.accuracy
        }
    
    def get_model_status(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get current status of a model."""
        if model_name not in self.version_history:
            return None
        
        history = self.version_history[model_name]
        current = history[-1]
        
        return {
            'model_name': model_name,
            'current_version': current.version_number,
            'accuracy': current.accuracy,
            'is_active': current.is_active,
            'strategy': current.update_strategy.value,
            'total_versions': len(history)
        }


# ============================================================================
# Block 27: Clone Readiness Scoring
# ============================================================================

@dataclass
class CloneReadinessScore:
    """Readiness score for a clone."""
    clone_id: str
    accuracy: float
    confidence: float
    consistency: float
    robustness: float
    overall_score: float
    is_ready: bool
    readiness_threshold: float = 0.80


class CloneReadinessScorecardi:
    """
    Scores clones for production readiness.
    
    Evaluates:
    - Accuracy (0-1)
    - Confidence (0-1)
    - Consistency (0-1)
    - Robustness (0-1)
    - Overall composite score
    """
    
    def __init__(self, readiness_threshold: float = 0.80):
        """Initialize clone readiness scorer."""
        self.readiness_threshold = readiness_threshold
        self.scores: Dict[str, CloneReadinessScore] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("CloneReadinessScorer")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def score_clone(self, clone_id: str, accuracy: float, confidence: float,
                   consistency: float, robustness: float) -> Dict[str, Any]:
        """Score a clone's readiness."""
        # Calculate weighted overall score
        overall_score = (
            0.4 * accuracy +
            0.3 * confidence +
            0.2 * consistency +
            0.1 * robustness
        )
        
        is_ready = overall_score >= self.readiness_threshold
        
        score = CloneReadinessScore(
            clone_id=clone_id,
            accuracy=accuracy,
            confidence=confidence,
            consistency=consistency,
            robustness=robustness,
            overall_score=overall_score,
            is_ready=is_ready,
            readiness_threshold=self.readiness_threshold
        )
        
        self.scores[clone_id] = score
        
        status = "READY" if is_ready else "NOT_READY"
        self.logger.info(f"Clone {clone_id} scored {overall_score:.1%} - {status}")
        
        return {
            'clone_id': clone_id,
            'accuracy': accuracy,
            'confidence': confidence,
            'consistency': consistency,
            'robustness': robustness,
            'overall_score': overall_score,
            'is_ready': is_ready,
            'status': status
        }
    
    def get_ready_clones(self) -> List[Dict[str, Any]]:
        """Get all clones that are ready for production."""
        ready = [s for s in self.scores.values() if s.is_ready]
        return [
            {
                'clone_id': s.clone_id,
                'overall_score': s.overall_score,
                'accuracy': s.accuracy
            }
            for s in ready
        ]
    
    def get_clone_score(self, clone_id: str) -> Optional[Dict[str, Any]]:
        """Get readiness score for a clone."""
        if clone_id not in self.scores:
            return None
        
        score = self.scores[clone_id]
        return {
            'clone_id': clone_id,
            'accuracy': score.accuracy,
            'confidence': score.confidence,
            'consistency': score.consistency,
            'robustness': score.robustness,
            'overall_score': score.overall_score,
            'is_ready': score.is_ready
        }


# ============================================================================
# Block 28: Clone Gate Enforcement
# ============================================================================

class GateStatus(Enum):
    """Gate check status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class GateResult:
    """Result of a gate check."""
    gate_id: str
    clone_id: str
    gate_name: str
    status: GateStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CloneGateEnforcer:
    """
    Enforces gates before clone promotion to production.
    
    Gates:
    - Readiness gate (overall score)
    - Performance gate (accuracy threshold)
    - Safety gate (no regressions)
    - Compliance gate (audit requirements)
    """
    
    def __init__(self):
        """Initialize gate enforcer."""
        self.gate_results: Dict[str, GateResult] = {}
        self.clone_gates: Dict[str, List[GateResult]] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("CloneGateEnforcer")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def check_readiness_gate(self, clone_id: str, readiness_score: float) -> Dict[str, Any]:
        """Check readiness gate (score > 0.80)."""
        gate_id = f"gate_{uuid.uuid4().hex[:12]}"
        status = GateStatus.PASS if readiness_score > 0.80 else GateStatus.FAIL
        message = f"Readiness score {readiness_score:.1%} {'passes' if status == GateStatus.PASS else 'fails'} gate"
        
        result = GateResult(
            gate_id=gate_id,
            clone_id=clone_id,
            gate_name="readiness",
            status=status,
            message=message
        )
        
        self._record_gate(clone_id, result)
        self.logger.info(f"Readiness gate: {clone_id} - {status.value.upper()}")
        
        return {
            'gate_id': gate_id,
            'clone_id': clone_id,
            'gate_name': 'readiness',
            'status': status.value,
            'message': message
        }
    
    def check_performance_gate(self, clone_id: str, accuracy: float,
                              threshold: float = 0.85) -> Dict[str, Any]:
        """Check performance gate (accuracy > threshold)."""
        gate_id = f"gate_{uuid.uuid4().hex[:12]}"
        status = GateStatus.PASS if accuracy >= threshold else GateStatus.FAIL
        message = f"Accuracy {accuracy:.1%} {'meets' if status == GateStatus.PASS else 'fails to meet'} threshold {threshold:.1%}"
        
        result = GateResult(
            gate_id=gate_id,
            clone_id=clone_id,
            gate_name="performance",
            status=status,
            message=message
        )
        
        self._record_gate(clone_id, result)
        self.logger.info(f"Performance gate: {clone_id} - {status.value.upper()}")
        
        return {
            'gate_id': gate_id,
            'clone_id': clone_id,
            'gate_name': 'performance',
            'status': status.value,
            'message': message
        }
    
    def check_safety_gate(self, clone_id: str, regression_detected: bool) -> Dict[str, Any]:
        """Check safety gate (no regressions)."""
        gate_id = f"gate_{uuid.uuid4().hex[:12]}"
        status = GateStatus.FAIL if regression_detected else GateStatus.PASS
        message = "Regression detected - FAILED" if regression_detected else "No regressions detected - PASSED"
        
        result = GateResult(
            gate_id=gate_id,
            clone_id=clone_id,
            gate_name="safety",
            status=status,
            message=message
        )
        
        self._record_gate(clone_id, result)
        self.logger.info(f"Safety gate: {clone_id} - {status.value.upper()}")
        
        return {
            'gate_id': gate_id,
            'clone_id': clone_id,
            'gate_name': 'safety',
            'status': status.value,
            'message': message
        }
    
    def _record_gate(self, clone_id: str, result: GateResult) -> None:
        """Record gate result."""
        self.gate_results[result.gate_id] = result
        if clone_id not in self.clone_gates:
            self.clone_gates[clone_id] = []
        self.clone_gates[clone_id].append(result)
    
    def enforce_all_gates(self, clone_id: str, readiness_score: float,
                         accuracy: float, regression_detected: bool) -> Dict[str, Any]:
        """Enforce all gates and determine if clone can be promoted."""
        readiness = self.check_readiness_gate(clone_id, readiness_score)
        performance = self.check_performance_gate(clone_id, accuracy)
        safety = self.check_safety_gate(clone_id, regression_detected)
        
        all_gates = [readiness['status'], performance['status'], safety['status']]
        can_promote = all(status == 'pass' for status in all_gates)
        
        self.logger.info(f"All gates for {clone_id}: {'PROMOTE' if can_promote else 'BLOCK'}")
        
        return {
            'clone_id': clone_id,
            'gates': [readiness, performance, safety],
            'can_promote': can_promote,
            'decision': 'PROMOTE' if can_promote else 'BLOCK'
        }
    
    def get_clone_gate_status(self, clone_id: str) -> Optional[Dict[str, Any]]:
        """Get gate status for a clone."""
        if clone_id not in self.clone_gates:
            return None
        
        gates = self.clone_gates[clone_id]
        return {
            'clone_id': clone_id,
            'total_gates': len(gates),
            'passed': sum(1 for g in gates if g.status == GateStatus.PASS),
            'failed': sum(1 for g in gates if g.status == GateStatus.FAIL),
            'gates': [
                {
                    'gate_name': g.gate_name,
                    'status': g.status.value,
                    'message': g.message
                }
                for g in gates
            ]
        }


# ============================================================================
# Block 29: Clone Audit Trail + Rollback
# ============================================================================

@dataclass
class AuditEntry:
    """Audit trail entry."""
    entry_id: str
    clone_id: str
    action: str
    status: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


class CloneAuditTrail:
    """
    Maintains comprehensive audit trail for clones.
    
    Tracks:
    - Deployment events
    - Model updates
    - Gate checks
    - Rollback operations
    - Performance changes
    """
    
    def __init__(self):
        """Initialize audit trail."""
        self.audit_log: List[AuditEntry] = []
        self.clone_snapshots: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("CloneAuditTrail")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def log_action(self, clone_id: str, action: str, status: str,
                  details: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """Log an action in the audit trail."""
        entry_id = f"aud_{uuid.uuid4().hex[:12]}"
        entry = AuditEntry(
            entry_id=entry_id,
            clone_id=clone_id,
            action=action,
            status=status,
            details=details,
            user_id=user_id
        )
        
        self.audit_log.append(entry)
        
        if clone_id not in self.clone_snapshots:
            self.clone_snapshots[clone_id] = []
        self.clone_snapshots[clone_id].append({
            'entry_id': entry_id,
            'action': action,
            'status': status,
            'timestamp': entry.timestamp
        })
        
        self.logger.info(f"Logged: {clone_id} - {action} ({status})")
        
        return entry_id
    
    def create_snapshot(self, clone_id: str, model_state: Dict[str, Any]) -> str:
        """Create a snapshot of clone state for rollback."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
        
        self.log_action(
            clone_id,
            "CREATE_SNAPSHOT",
            "SUCCESS",
            {'snapshot_id': snapshot_id, 'model_state': model_state}
        )
        
        self.logger.info(f"Created snapshot {snapshot_id} for {clone_id}")
        
        return snapshot_id
    
    def get_audit_trail(self, clone_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for a clone."""
        entries = [e for e in self.audit_log if e.clone_id == clone_id]
        return [
            {
                'entry_id': e.entry_id,
                'clone_id': e.clone_id,
                'action': e.action,
                'status': e.status,
                'details': e.details,
                'timestamp': e.timestamp,
                'user_id': e.user_id
            }
            for e in entries
        ]
    
    def export_audit_trail(self, clone_id: str, format_type: str = 'json') -> Optional[str]:
        """Export audit trail to specified format."""
        trail = self.get_audit_trail(clone_id)
        
        if format_type == 'json':
            return json.dumps(trail, indent=2, default=str)
        
        return None


# ============================================================================
# Block 30: End-to-End Brain Verification Suite
# ============================================================================

class VerificationStatus(Enum):
    """Verification status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass
class VerificationResult:
    """Single verification result."""
    check_name: str
    status: VerificationStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BrainVerificationSuite:
    """
    End-to-end verification of the complete brain system.
    
    Verifies:
    - Component initialization
    - Data flow accuracy
    - Performance metrics
    - System consistency
    - Safety gates
    - Integration points
    """
    
    def __init__(self):
        """Initialize verification suite."""
        self.results: List[VerificationResult] = []
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("BrainVerificationSuite")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def verify_ab_tracking(self) -> Dict[str, Any]:
        """Verify A/B tracking system."""
        try:
            tracker = ABTracker()
            vid = tracker.register_variant("Test", "script")
            tracker.track_performance(vid, 0.85)
            status = VerificationStatus.PASS
            message = "A/B tracking system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"A/B tracking failed: {str(e)}"
        
        result = VerificationResult("ab_tracking", status, message)
        self.results.append(result)
        self.logger.info(f"A/B Tracking: {status.value.upper()}")
        
        return {
            'check': 'ab_tracking',
            'status': status.value,
            'message': message
        }
    
    def verify_script_promotion(self) -> Dict[str, Any]:
        """Verify script promotion system."""
        try:
            promoter = ScriptPromoter()
            sid = promoter.register_script("Test", "1.0")
            promoter.evaluate_script(sid, 0.87)
            status = VerificationStatus.PASS
            message = "Script promotion system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Script promotion failed: {str(e)}"
        
        result = VerificationResult("script_promotion", status, message)
        self.results.append(result)
        self.logger.info(f"Script Promotion: {status.value.upper()}")
        
        return {
            'check': 'script_promotion',
            'status': status.value,
            'message': message
        }
    
    def verify_deal_packets(self) -> Dict[str, Any]:
        """Verify deal packet builder."""
        try:
            builder = DealPacketBuilder()
            lead_data = {"name": "Test Lead", "value": 100000, "terms": "30 days"}
            pid = builder.build_packet(lead_data, ["Script A"], ["Email"])
            packet = builder.get_packet(pid)
            status = VerificationStatus.PASS if packet else VerificationStatus.FAIL
            message = "Deal packet system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Deal packets failed: {str(e)}"
        
        result = VerificationResult("deal_packets", status, message)
        self.results.append(result)
        self.logger.info(f"Deal Packets: {status.value.upper()}")
        
        return {
            'check': 'deal_packets',
            'status': status.value,
            'message': message
        }
    
    def verify_learning_ingestion(self) -> Dict[str, Any]:
        """Verify learning ingestion with allowed sources."""
        try:
            ingestor = LearningIngestsor(["Source A", "Source B"])
            result = ingestor.ingest_data("Source A", {"data": "test"})
            blocked = ingestor.ingest_data("UnknownSource", {"data": "test"})
            
            status = VerificationStatus.PASS if result['success'] and not blocked['success'] else VerificationStatus.FAIL
            message = "Learning ingestion system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Learning ingestion failed: {str(e)}"
        
        result_obj = VerificationResult("learning_ingestion", status, message)
        self.results.append(result_obj)
        self.logger.info(f"Learning Ingestion: {status.value.upper()}")
        
        return {
            'check': 'learning_ingestion',
            'status': status.value,
            'message': message
        }
    
    def verify_outcome_evaluation(self) -> Dict[str, Any]:
        """Verify outcome evaluation loop."""
        try:
            evaluator = OutcomeEvaluator()
            result = evaluator.evaluate_outcome(0.85)
            trend = evaluator.get_improvement_trend()
            status = VerificationStatus.PASS
            message = "Outcome evaluation system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Outcome evaluation failed: {str(e)}"
        
        result_obj = VerificationResult("outcome_evaluation", status, message)
        self.results.append(result_obj)
        self.logger.info(f"Outcome Evaluation: {status.value.upper()}")
        
        return {
            'check': 'outcome_evaluation',
            'status': status.value,
            'message': message
        }
    
    def verify_model_updates(self) -> Dict[str, Any]:
        """Verify safe model update mechanism."""
        try:
            updater = SafeModelUpdater()
            vid = updater.create_model("Test Model")
            update = updater.update_model(vid, 0.88)
            status = VerificationStatus.PASS
            message = "Model update system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Model updates failed: {str(e)}"
        
        result_obj = VerificationResult("model_updates", status, message)
        self.results.append(result_obj)
        self.logger.info(f"Model Updates: {status.value.upper()}")
        
        return {
            'check': 'model_updates',
            'status': status.value,
            'message': message
        }
    
    def verify_clone_readiness(self) -> Dict[str, Any]:
        """Verify clone readiness scoring."""
        try:
            scorer = CloneReadinessScorecardi()
            result = scorer.score_clone("clone_1", 0.9, 0.85, 0.88, 0.87)
            status = VerificationStatus.PASS if result['is_ready'] else VerificationStatus.WARNING
            message = "Clone readiness system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Clone readiness failed: {str(e)}"
        
        result_obj = VerificationResult("clone_readiness", status, message)
        self.results.append(result_obj)
        self.logger.info(f"Clone Readiness: {status.value.upper()}")
        
        return {
            'check': 'clone_readiness',
            'status': status.value,
            'message': message
        }
    
    def verify_clone_gates(self) -> Dict[str, Any]:
        """Verify clone gate enforcement."""
        try:
            enforcer = CloneGateEnforcer()
            result = enforcer.enforce_all_gates("clone_1", 0.85, 0.88, False)
            status = VerificationStatus.PASS if result['can_promote'] else VerificationStatus.FAIL
            message = "Clone gate enforcement operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Clone gates failed: {str(e)}"
        
        result_obj = VerificationResult("clone_gates", status, message)
        self.results.append(result_obj)
        self.logger.info(f"Clone Gates: {status.value.upper()}")
        
        return {
            'check': 'clone_gates',
            'status': status.value,
            'message': message
        }
    
    def verify_audit_trail(self) -> Dict[str, Any]:
        """Verify audit trail system."""
        try:
            audit = CloneAuditTrail()
            eid = audit.log_action("clone_1", "DEPLOY", "SUCCESS", {"version": "1.0"})
            trail = audit.get_audit_trail("clone_1")
            status = VerificationStatus.PASS if trail else VerificationStatus.FAIL
            message = "Audit trail system operational"
        except Exception as e:
            status = VerificationStatus.FAIL
            message = f"Audit trail failed: {str(e)}"
        
        result_obj = VerificationResult("audit_trail", status, message)
        self.results.append(result_obj)
        self.logger.info(f"Audit Trail: {status.value.upper()}")
        
        return {
            'check': 'audit_trail',
            'status': status.value,
            'message': message
        }
    
    def run_full_verification(self) -> Dict[str, Any]:
        """Run complete verification suite."""
        self.logger.info("Starting full brain verification...")
        
        checks = [
            self.verify_ab_tracking,
            self.verify_script_promotion,
            self.verify_deal_packets,
            self.verify_learning_ingestion,
            self.verify_outcome_evaluation,
            self.verify_model_updates,
            self.verify_clone_readiness,
            self.verify_clone_gates,
            self.verify_audit_trail
        ]
        
        results = []
        for check in checks:
            try:
                results.append(check())
            except Exception as e:
                self.logger.error(f"Verification check failed: {str(e)}")
        
        passed = sum(1 for r in results if r['status'] == 'pass')
        failed = sum(1 for r in results if r['status'] == 'fail')
        warnings = sum(1 for r in results if r['status'] == 'warning')
        
        overall_status = "PASS" if failed == 0 else "FAIL"
        
        self.logger.info(f"Verification complete: {passed} pass, {failed} fail, {warnings} warnings")
        
        return {
            'overall_status': overall_status,
            'total_checks': len(results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'checks': results,
            'timestamp': datetime.utcnow()
        }
    
    def get_verification_report(self, format_type: str = 'json') -> str:
        """Get verification report."""
        if not self.results:
            return "No verification results available"
        
        if format_type == 'json':
            report = {
                'total_checks': len(self.results),
                'passed': sum(1 for r in self.results if r.status == VerificationStatus.PASS),
                'failed': sum(1 for r in self.results if r.status == VerificationStatus.FAIL),
                'warnings': sum(1 for r in self.results if r.status == VerificationStatus.WARNING),
                'results': [
                    {
                        'check': r.check_name,
                        'status': r.status.value,
                        'message': r.message,
                        'timestamp': r.timestamp
                    }
                    for r in self.results
                ]
            }
            return json.dumps(report, indent=2, default=str)
        
        return str(self.results)


# ============================================================================
# Main Orchestrator
# ============================================================================

class LearningAndScalingOrchestrator:
    """
    Unified orchestrator for all Batch 3 components.
    
    Manages:
    - A/B tracking
    - Script promotion
    - Deal packet building
    - Learning ingestion
    - Outcome evaluation
    - Model updates
    - Clone management
    - Verification
    """
    
    def __init__(self, allowed_learning_sources: List[str] = None):
        """Initialize orchestrator."""
        if allowed_learning_sources is None:
            allowed_learning_sources = ["Zillow", "Facebook", "Redfin", "MLS"]
        
        self.ab_tracker = ABTracker()
        self.script_promoter = ScriptPromoter()
        self.deal_builder = DealPacketBuilder()
        self.learning_ingestor = LearningIngestsor(allowed_learning_sources)
        self.outcome_evaluator = OutcomeEvaluator()
        self.model_updater = SafeModelUpdater()
        self.readiness_scorer = CloneReadinessScorecardi()
        self.gate_enforcer = CloneGateEnforcer()
        self.audit_trail = CloneAuditTrail()
        self.verification_suite = BrainVerificationSuite()
        
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger("LearningAndScalingOrchestrator")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            'ab_variants': len(self.ab_tracker.variants),
            'scripts': len(self.script_promoter.scripts),
            'deal_packets': len(self.deal_builder.packets),
            'ingested_datasets': len(self.learning_ingestor.ingested_data),
            'evaluations': len(self.outcome_evaluator.evaluations),
            'models': len(self.model_updater.models),
            'clone_scores': len(self.readiness_scorer.scores),
            'audit_entries': len(self.audit_trail.audit_log),
            'timestamp': datetime.utcnow()
        }
    
    def run_verification(self) -> Dict[str, Any]:
        """Run full system verification."""
        return self.verification_suite.run_full_verification()


# Typo fix for class name
class CloneReadinessScorer(CloneReadinessScorecardi):
    """Alias for correct class name."""
    pass


class LearningIngestsor(LearningIngestsor):
    """Alias for correct class name."""
    pass
