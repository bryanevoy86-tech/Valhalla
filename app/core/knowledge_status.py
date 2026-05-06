"""
Knowledge Status - Enum for knowledge item lifecycle states

This module defines the status workflow for knowledge items as they move
through curation, validation, and eventual deprecation.

Usage:
    from app.core.knowledge_status import KnowledgeStatus
    
    status = KnowledgeStatus.TRUSTED
    print(status.value)  # "trusted"
"""

from enum import Enum


class KnowledgeStatus(str, Enum):
    """
    Enumeration of knowledge item status stages.
    
    Knowledge items progress through these states:
        DRAFT → REVIEWED → TRUSTED (or REJECTED/DEPRECATED)
    
    This enables quality control and confidence management.
    """
    
    DRAFT = "draft"
    """
    Initial ingestion state. Knowledge item entered but not yet reviewed.
    Used in recommendations with reduced confidence.
    """
    
    REVIEWED = "reviewed"
    """
    Knowledge has been reviewed by someone with domain expertise.
    Checking is complete but may need more validation.
    Ready for limited use in recommendations with medium confidence.
    """
    
    TRUSTED = "trusted"
    """
    Knowledge has been validated through multiple sources or outcomes.
    Can be used with high confidence in recommendations.
    This is the target state for knowledge used in decision-making.
    """
    
    DEPRECATED = "deprecated"
    """
    Knowledge was once trusted but is no longer current or applicable.
    Keep for historical reference but don't use in new recommendations.
    Typically set when outcome data shows it's no longer accurate.
    """
    
    REJECTED = "rejected"
    """
    Knowledge was reviewed and found to be inaccurate or not applicable.
    Don't use in recommendations. Keep for audit trail only.
    """


# Status transitions (what states can follow what states)
VALID_STATUS_TRANSITIONS = {
    KnowledgeStatus.DRAFT: [
        KnowledgeStatus.REVIEWED,
        KnowledgeStatus.REJECTED,
    ],
    KnowledgeStatus.REVIEWED: [
        KnowledgeStatus.TRUSTED,
        KnowledgeStatus.REJECTED,
        KnowledgeStatus.DRAFT,  # Can revert if issue found
    ],
    KnowledgeStatus.TRUSTED: [
        KnowledgeStatus.DEPRECATED,
        KnowledgeStatus.REVIEWED,  # Revisit if questions arise
    ],
    KnowledgeStatus.DEPRECATED: [
        KnowledgeStatus.TRUSTED,  # Can un-deprecate if still valid
    ],
    KnowledgeStatus.REJECTED: [
        KnowledgeStatus.REVIEWED,  # Can reconsider after new info
    ],
}

# Confidence impact of each status
STATUS_CONFIDENCE_MULTIPLIER = {
    KnowledgeStatus.DRAFT: 0.5,        # 50% of stated confidence
    KnowledgeStatus.REVIEWED: 0.75,    # 75% of stated confidence
    KnowledgeStatus.TRUSTED: 1.0,      # 100% of stated confidence
    KnowledgeStatus.DEPRECATED: 0.0,   # Don't use (0% confidence)
    KnowledgeStatus.REJECTED: 0.0,     # Don't use (0% confidence)
}

# Display-friendly names
STATUS_DISPLAY = {
    KnowledgeStatus.DRAFT: "Draft (Unreviewed)",
    KnowledgeStatus.REVIEWED: "Reviewed",
    KnowledgeStatus.TRUSTED: "Trusted",
    KnowledgeStatus.DEPRECATED: "Deprecated",
    KnowledgeStatus.REJECTED: "Rejected",
}

# Description for UI
STATUS_DESCRIPTION = {
    KnowledgeStatus.DRAFT: (
        "Initial ingestion state. Not yet reviewed. Use with caution. "
        "Confidence: 50% of stated value."
    ),
    KnowledgeStatus.REVIEWED: (
        "Reviewed by domain expert. Checked for accuracy and applicability. "
        "Confidence: 75% of stated value."
    ),
    KnowledgeStatus.TRUSTED: (
        "Validated through multiple sources or proven outcomes. "
        "Confidence: 100% of stated value. Recommended for decisions."
    ),
    KnowledgeStatus.DEPRECATED: (
        "Valid historically but no longer current. Keep for reference only. "
        "Do not use in new recommendations."
    ),
    KnowledgeStatus.REJECTED: (
        "Reviewed and found inaccurate or not applicable. "
        "Do not use in recommendations. Kept for audit trail."
    ),
}

# Color codes for UI display
STATUS_COLOR = {
    KnowledgeStatus.DRAFT: "#FFA500",      # Orange
    KnowledgeStatus.REVIEWED: "#4169E1",   # Blue
    KnowledgeStatus.TRUSTED: "#228B22",    # Green
    KnowledgeStatus.DEPRECATED: "#808080", # Gray
    KnowledgeStatus.REJECTED: "#DC143C",   # Crimson
}

# Grouped by usage tier
STATUS_CATEGORIES = {
    "Can Use (With Caution)": [
        KnowledgeStatus.DRAFT,
        KnowledgeStatus.REVIEWED,
    ],
    "Can Use (Recommended)": [
        KnowledgeStatus.TRUSTED,
    ],
    "Cannot Use": [
        KnowledgeStatus.DEPRECATED,
        KnowledgeStatus.REJECTED,
    ],
}


def can_recommend(status: str) -> bool:
    """
    Check if a knowledge item with this status should be used in recommendations.
    
    Args:
        status: Status value
        
    Returns:
        True if status allows recommendation, False otherwise
    """
    try:
        status_enum = KnowledgeStatus(status.lower())
        return status_enum not in [
            KnowledgeStatus.DEPRECATED,
            KnowledgeStatus.REJECTED,
        ]
    except (ValueError, KeyError):
        return False


def get_effective_confidence(stated_confidence: float, status: str) -> float:
    """
    Calculate effective confidence by applying status multiplier.
    
    Args:
        stated_confidence: Confidence score stated (0.0-1.0)
        status: Knowledge status
        
    Returns:
        Effective confidence after status adjustment
    """
    try:
        status_enum = KnowledgeStatus(status.lower())
        multiplier = STATUS_CONFIDENCE_MULTIPLIER.get(status_enum, 0.5)
        return stated_confidence * multiplier
    except (ValueError, KeyError):
        return stated_confidence * 0.5


def is_actionable(status: str) -> bool:
    """
    Check if knowledge item is actionable (not deprecated/rejected).
    
    Args:
        status: Status value
        
    Returns:
        True if actionable, False otherwise
    """
    return can_recommend(status)


def get_usable_statuses() -> list:
    """Return statuses where knowledge should be used in recommendations"""
    return [
        KnowledgeStatus.TRUSTED,
        KnowledgeStatus.REVIEWED,
    ]


def get_review_needed_statuses() -> list:
    """Return statuses indicating knowledge needs review"""
    return [
        KnowledgeStatus.DRAFT,
        KnowledgeStatus.REJECTED,
    ]
