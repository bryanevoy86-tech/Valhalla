"""
Knowledge Types - Enum for categorizing knowledge items

This module defines what types of knowledge can be stored in Heimdall Intelligence Layer.
Each type represents a distinct category of operational knowledge that informs decisions.

Usage:
    from app.core.knowledge_types import KnowledgeType
    
    knowledge_type = KnowledgeType.REHAB_COST
    print(knowledge_type.value)  # "rehab_cost"
"""

from enum import Enum


class KnowledgeType(str, Enum):
    """
    Enumeration of knowledge types that can be stored in Heimdall Intelligence.
    
    These categories enable classification and filtering of knowledge items
    for targeted recommendations and learning.
    """
    
    # Cost-related knowledge
    REHAB_COST = "rehab_cost"
    """Estimated costs for specific property repairs/renovations"""
    
    # Market knowledge
    MARKET_TREND = "market_trend"
    """Regional market patterns, cycles, and structural changes"""
    
    # Negotiation knowledge
    NEGOTIATION_PATTERN = "negotiation_pattern"
    """Buyer/seller/partner negotiation behavior and patterns"""
    
    # Legal/regulatory knowledge
    LEGAL_CONSTRAINT = "legal_constraint"
    """Legal, regulatory, or compliance requirements"""
    
    # Lead source knowledge
    LEAD_SOURCE_PATTERN = "lead_source_pattern"
    """Patterns, quality, and characteristics of lead sources"""
    
    # Buyer knowledge
    BUYER_BEHAVIOR = "buyer_behavior"
    """How buyers in a market behave and make decisions"""
    
    # Seller knowledge
    SELLER_BEHAVIOR = "seller_behavior"
    """How sellers in a market behave and make decisions"""
    
    # Valuation knowledge
    RENT_ESTIMATE = "rent_estimate"
    """Estimated rental rates for properties"""
    
    ARV_ESTIMATE = "arv_estimate"
    """After-repair value estimates and valuation patterns"""
    
    # Financing knowledge
    FINANCING_PATTERN = "financing_pattern"
    """Available financing options, terms, and lending patterns"""
    
    # Tax knowledge
    TAX_RULE = "tax_rule"
    """Tax implications, deductions, and strategic tax planning"""
    
    # Operational knowledge
    OPERATIONAL_RULE = "operational_rule"
    """Operational constraints, best practices, and workflow knowledge"""


# Display-friendly names for UI
KNOWLEDGE_TYPE_DISPLAY = {
    KnowledgeType.REHAB_COST: "Rehab Cost Estimates",
    KnowledgeType.MARKET_TREND: "Market Trends",
    KnowledgeType.NEGOTIATION_PATTERN: "Negotiation Patterns",
    KnowledgeType.LEGAL_CONSTRAINT: "Legal Constraints",
    KnowledgeType.LEAD_SOURCE_PATTERN: "Lead Source Patterns",
    KnowledgeType.BUYER_BEHAVIOR: "Buyer Behavior",
    KnowledgeType.SELLER_BEHAVIOR: "Seller Behavior",
    KnowledgeType.RENT_ESTIMATE: "Rent Estimates",
    KnowledgeType.ARV_ESTIMATE: "ARV Estimates",
    KnowledgeType.FINANCING_PATTERN: "Financing Patterns",
    KnowledgeType.TAX_RULE: "Tax Rules",
    KnowledgeType.OPERATIONAL_RULE: "Operational Rules",
}


# Grouped by category for UI/filtering
KNOWLEDGE_TYPE_CATEGORIES = {
    "Cost & Valuation": [
        KnowledgeType.REHAB_COST,
        KnowledgeType.ARV_ESTIMATE,
        KnowledgeType.RENT_ESTIMATE,
    ],
    "Market": [
        KnowledgeType.MARKET_TREND,
        KnowledgeType.BUYER_BEHAVIOR,
        KnowledgeType.SELLER_BEHAVIOR,
    ],
    "Deal Structure": [
        KnowledgeType.NEGOTIATION_PATTERN,
        KnowledgeType.FINANCING_PATTERN,
        KnowledgeType.LEGAL_CONSTRAINT,
    ],
    "Sourcing & Operations": [
        KnowledgeType.LEAD_SOURCE_PATTERN,
        KnowledgeType.OPERATIONAL_RULE,
        KnowledgeType.TAX_RULE,
    ],
}


def get_knowledge_types_for_strategy(strategy: str) -> list:
    """
    Return recommended knowledge types for a given strategy.
    
    Args:
        strategy: Strategy code (e.g., "wholesale", "hold")
        
    Returns:
        List of relevant KnowledgeType values
    """
    strategy_knowledge_map = {
        "wholesale": [
            KnowledgeType.REHAB_COST,
            KnowledgeType.ARV_ESTIMATE,
            KnowledgeType.NEGOTIATION_PATTERN,
            KnowledgeType.BUYER_BEHAVIOR,
            KnowledgeType.LEAD_SOURCE_PATTERN,
        ],
        "hold": [
            KnowledgeType.MARKET_TREND,
            KnowledgeType.RENT_ESTIMATE,
            KnowledgeType.FINANCING_PATTERN,
            KnowledgeType.TAX_RULE,
            KnowledgeType.OPERATIONAL_RULE,
        ],
        "flip": [
            KnowledgeType.REHAB_COST,
            KnowledgeType.ARV_ESTIMATE,
            KnowledgeType.MARKET_TREND,
            KnowledgeType.FINANCING_PATTERN,
            KnowledgeType.LEGAL_CONSTRAINT,
        ],
        "partnership": [
            KnowledgeType.NEGOTIATION_PATTERN,
            KnowledgeType.LEGAL_CONSTRAINT,
            KnowledgeType.SELLER_BEHAVIOR,
            KnowledgeType.FINANCING_PATTERN,
            KnowledgeType.TAX_RULE,
        ],
    }
    return strategy_knowledge_map.get(strategy.lower(), [])
