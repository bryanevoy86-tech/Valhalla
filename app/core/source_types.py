"""
Source Types - Enum for categorizing knowledge sources

This module defines what types of sources knowledge can come from.
The source type directly influences trust level assessment.

Usage:
    from app.core.source_types import SourceType
    
    source_type = SourceType.GOVERNMENT
    print(source_type.value)  # "government"
"""

from enum import Enum


class SourceType(str, Enum):
    """
    Enumeration of knowledge source types.
    
    These categories indicate where the knowledge came from,
    which informs confidence assessment and trust level.
    """
    
    # Authoritative/Official sources
    GOVERNMENT = "government"
    """Government agencies, assessors, courts, regulatory bodies"""
    
    # Public information
    PUBLIC_WEB = "public_web"
    """Publicly available web sources (blogs, news, reports)"""
    
    FORUM = "forum"
    """Online forums and discussion communities (REI, Facebook, etc.)"""
    
    COMMUNITY = "community"
    """Local community organizations (REIA chapters, meetups)"""
    
    # Published analysis
    MARKET_REPORT = "market_report"
    """Professional market analysis reports (CoStar, Zillow, etc.)"""
    
    # Internal sources
    INTERNAL_OUTCOME = "internal_outcome"
    """Results from our own completed deals and operations"""
    
    OPERATOR_NOTE = "operator_note"
    """Direct notes from team members and operators"""
    
    # Imported content
    IMPORTED_DOC = "imported_doc"
    """Imported documents, templates, or knowledge bases"""


# Trust level associations by source type
# (Default trust_level assignment based on source type)
SOURCE_TYPE_DEFAULT_TRUST = {
    SourceType.GOVERNMENT: "high",
    SourceType.MARKET_REPORT: "high",
    SourceType.INTERNAL_OUTCOME: "high",
    SourceType.PUBLIC_WEB: "medium",
    SourceType.FORUM: "medium",
    SourceType.COMMUNITY: "medium",
    SourceType.OPERATOR_NOTE: "medium",
    SourceType.IMPORTED_DOC: "medium",
}

# Display-friendly names for UI
SOURCE_TYPE_DISPLAY = {
    SourceType.GOVERNMENT: "Government (Assessor, Court, Regulatory)",
    SourceType.PUBLIC_WEB: "Public Web Sources",
    SourceType.FORUM: "Online Forums & Communities",
    SourceType.COMMUNITY: "Local Community Organizations",
    SourceType.MARKET_REPORT: "Professional Market Reports",
    SourceType.INTERNAL_OUTCOME: "Our Operational Outcomes",
    SourceType.OPERATOR_NOTE: "Team Member Notes",
    SourceType.IMPORTED_DOC: "Imported Documents & Knowledge",
}

# Description for context
SOURCE_TYPE_DESCRIPTION = {
    SourceType.GOVERNMENT: (
        "Official government data from assessors, courts, and regulatory agencies. "
        "Highly reliable for public records and legal requirements."
    ),
    SourceType.PUBLIC_WEB: (
        "Publicly available web sources including news, blog posts, and analysis. "
        "Reliable for trends but verify specific claims."
    ),
    SourceType.FORUM: (
        "Community forum discussion (REI forums, Facebook groups, etc.). "
        "Useful for practitioner insights but verify with multiple sources."
    ),
    SourceType.COMMUNITY: (
        "Local community organizations like REIA chapters and networking groups. "
        "Good for regional insights and networking."
    ),
    SourceType.MARKET_REPORT: (
        "Professional market analysis from services like CoStar, Zillow, CoreLogic. "
        "Highly reliable for market trends and valuation data."
    ),
    SourceType.INTERNAL_OUTCOME: (
        "Results from our own completed deals and operations. "
        "Highest reliability for our specific market/strategy performance."
    ),
    SourceType.OPERATOR_NOTE: (
        "Direct observations and notes from our team members. "
        "Valuable for lessons learned and operational insights."
    ),
    SourceType.IMPORTED_DOC: (
        "Documents we import (templates, guides, reference materials). "
        "Usefulness depends on original source."
    ),
}

# Grouped by category for UI/filtering
SOURCE_TYPE_CATEGORIES = {
    "Official Data": [
        SourceType.GOVERNMENT,
        SourceType.MARKET_REPORT,
    ],
    "Community & Web": [
        SourceType.FORUM,
        SourceType.COMMUNITY,
        SourceType.PUBLIC_WEB,
    ],
    "Internal Knowledge": [
        SourceType.INTERNAL_OUTCOME,
        SourceType.OPERATOR_NOTE,
    ],
    "Reference Material": [
        SourceType.IMPORTED_DOC,
    ],
}


def get_source_types_by_trust(trust_level: str) -> list:
    """
    Return which source types typically have a given trust level.
    
    Args:
        trust_level: "high", "medium", or "low"
        
    Returns:
        List of SourceType values
    """
    high_trust = [
        SourceType.GOVERNMENT,
        SourceType.MARKET_REPORT,
        SourceType.INTERNAL_OUTCOME,
    ]
    medium_trust = [
        SourceType.PUBLIC_WEB,
        SourceType.FORUM,
        SourceType.COMMUNITY,
        SourceType.OPERATOR_NOTE,
        SourceType.IMPORTED_DOC,
    ]
    
    if trust_level == "high":
        return high_trust
    elif trust_level == "medium":
        return medium_trust
    else:
        return []
