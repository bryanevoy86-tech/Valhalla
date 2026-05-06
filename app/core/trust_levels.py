"""
Trust Levels - Enum for source reliability assessment

This module defines trust levels for knowledge sources, influencing how confident
the system should be in applying that knowledge.

Usage:
    from app.core.trust_levels import TrustLevel
    
    trust = TrustLevel.HIGH
    print(trust.value)  # "high"
"""

from enum import Enum


class TrustLevel(str, Enum):
    """
    Enumeration of trust levels for knowledge sources.
    
    Trust level directly affects:
    - Default confidence score for knowledge items
    - How prominently the knowledge appears in recommendations
    - Requirement for additional validation before use
    """
    
    HIGH = "high"
    """
    Highly reliable source (government, market reports, internal outcomes).
    Can be used immediately in recommendations.
    Default confidence: 0.85+
    """
    
    MEDIUM = "medium"
    """
    Moderately reliable source (forums, community, operator notes).
    Should be used with context; consider validating with additional sources.
    Default confidence: 0.65-0.75
    """
    
    LOW = "low"
    """
    Lower reliability source (unverified web content, single anecdote).
    Use with caution; recommend validating before decisions.
    Default confidence: 0.40-0.55
    """


# Default confidence score by trust level
TRUST_LEVEL_DEFAULT_CONFIDENCE = {
    TrustLevel.HIGH: 0.85,
    TrustLevel.MEDIUM: 0.70,
    TrustLevel.LOW: 0.45,
}

# Minimum confidence for recommendations by trust level
TRUST_LEVEL_MIN_RECOMMENDATION_CONFIDENCE = {
    TrustLevel.HIGH: 0.75,      # Can recommend if confidence > 0.75
    TrustLevel.MEDIUM: 0.80,    # Need higher confidence for medium trust
    TrustLevel.LOW: 0.90,       # Very high confidence needed for low trust
}

# Display-friendly descriptions
TRUST_LEVEL_DESCRIPTION = {
    TrustLevel.HIGH: (
        "Highly reliable source (government data, professional reports, verified outcomes). "
        "Can be used in recommendations with confidence. Requires occasional spot-checking."
    ),
    TrustLevel.MEDIUM: (
        "Moderately reliable source (community/forum, operator notes, industry reports). "
        "Good for context; recommend cross-referencing with other sources."
    ),
    TrustLevel.LOW: (
        "Lower reliability source (unverified web content, single anecdote, opinion). "
        "Use carefully; validate with additional sources before acting on."
    ),
}

# Color codes for UI
TRUST_LEVEL_COLOR = {
    TrustLevel.HIGH: "#228B22",    # Green
    TrustLevel.MEDIUM: "#FFA500",  # Orange
    TrustLevel.LOW: "#DC143C",     # Crimson
}

# Icon representation
TRUST_LEVEL_ICON = {
    TrustLevel.HIGH: "✓",
    TrustLevel.MEDIUM: "≈",       # Approximately
    TrustLevel.LOW: "?",
}


def get_confidence_adjustment(trust_level: str) -> float:
    """
    Get confidence adjustment factor for this trust level.
    
    Used as multiplier: actual_confidence = stated_confidence * adjustment
    
    Args:
        trust_level: Trust level string
        
    Returns:
        Adjustment factor (0.5 to 1.0)
    """
    adjustments = {
        TrustLevel.HIGH: 1.0,      # No adjustment
        TrustLevel.MEDIUM: 0.85,   # Slight reduction
        TrustLevel.LOW: 0.60,      # Significant reduction
    }
    
    try:
        level = TrustLevel(trust_level.lower())
        return adjustments.get(level, 0.70)
    except (ValueError, KeyError):
        return 0.70


def should_use_in_recommendation(trust_level: str, confidence_score: float) -> bool:
    """
    Check if knowledge with this trust level and confidence should be used in recommendations.
    
    Args:
        trust_level: Trust level of the source
        confidence_score: Stated confidence (0.0-1.0)
        
    Returns:
        True if appropriate for recommendations
    """
    try:
        level = TrustLevel(trust_level.lower())
        required_confidence = TRUST_LEVEL_MIN_RECOMMENDATION_CONFIDENCE.get(level, 0.75)
        return confidence_score >= required_confidence
    except (ValueError, KeyError):
        return confidence_score >= 0.75


def get_trust_level_rank_by_source_type(source_type: str) -> str:
    """
    Recommend a trust level based on source type.
    
    Args:
        source_type: Type of source (government, forum, etc.)
        
    Returns:
        Recommended trust level
    """
    source_type_trust = {
        "government": TrustLevel.HIGH,
        "market_report": TrustLevel.HIGH,
        "internal_outcome": TrustLevel.HIGH,
        "public_web": TrustLevel.MEDIUM,
        "forum": TrustLevel.MEDIUM,
        "community": TrustLevel.MEDIUM,
        "operator_note": TrustLevel.MEDIUM,
        "imported_doc": TrustLevel.MEDIUM,
    }
    
    return source_type_trust.get(source_type.lower(), TrustLevel.MEDIUM)
