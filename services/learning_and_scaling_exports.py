"""
Learning and Scaling Module - Export Wrapper
Re-exports necessary classes for sandbox activation
"""

from services.learning_and_scaling import (
    ABTracker,
    ScriptPromoter,
    DealPacketBuilder,
    LearningIngestor,
    OutcomeEvaluator,
    SafeModelUpdater,
    CloneReadinessScorecardi,
    CloneGateEnforcer,
    CloneAuditTrail,
    BrainVerificationSuite,
    LearningAndScalingOrchestrator
)

# Fix class name aliasing
CloneReadinessScorer = CloneReadinessScorecardi

__all__ = [
    "ABTracker",
    "ScriptPromoter",
    "DealPacketBuilder",
    "LearningIngestor",
    "OutcomeEvaluator",
    "SafeModelUpdater",
    "CloneReadinessScorer",
    "CloneGateEnforcer",
    "CloneAuditTrail",
    "BrainVerificationSuite",
    "LearningAndScalingOrchestrator"
]
