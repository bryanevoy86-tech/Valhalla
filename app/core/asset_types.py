"""
Asset Types - Enum for real estate asset categories

This module defines the types of real estate assets that Heimdall Intelligence
can track and learn about.

Usage:
    from app.core.asset_types import AssetType
    
    asset = AssetType.SINGLE_FAMILY
    print(asset.value)  # "single_family"
"""

from enum import Enum


class AssetType(str, Enum):
    """
    Enumeration of real estate asset types.
    
    Used for categorizing knowledge, tracking deals,
    and making strategy-specific recommendations.
    """
    
    # Residential
    SINGLE_FAMILY = "single_family"
    """Single-family residential property (1-4 unit detached)"""
    
    MULTIFAMILY = "multifamily"
    """Multifamily residential (5+ units, apartments)"""
    
    MOBILE_HOME = "mobile_home"
    """Mobile home or mobile home park"""
    
    # Commercial
    OFFICE = "office"
    """Office building or office space"""
    
    RETAIL = "retail"
    """Retail property (storefront, shopping center)"""
    
    INDUSTRIAL = "industrial"
    """Industrial building or warehouse"""
    
    HOSPITALITY = "hospitality"
    """Hotel, resort, or hospitality property"""
    
    # Specialty
    LAND = "land"
    """Raw land or vacant land"""
    
    MIXED_USE = "mixed_use"
    """Mixed-use property (residential + commercial)"""
    
    SPECIAL_USE = "special_use"
    """Special purpose property (church, government, etc.)"""


# Display-friendly names
ASSET_TYPE_DISPLAY = {
    AssetType.SINGLE_FAMILY: "Single Family Home",
    AssetType.MULTIFAMILY: "Multifamily Apartments",
    AssetType.MOBILE_HOME: "Mobile Home",
    AssetType.OFFICE: "Office",
    AssetType.RETAIL: "Retail",
    AssetType.INDUSTRIAL: "Industrial / Warehouse",
    AssetType.HOSPITALITY: "Hotel / Resort",
    AssetType.LAND: "Land",
    AssetType.MIXED_USE: "Mixed Use",
    AssetType.SPECIAL_USE: "Special Purpose",
}

# Grouped by category
ASSET_TYPE_CATEGORIES = {
    "Residential": [
        AssetType.SINGLE_FAMILY,
        AssetType.MULTIFAMILY,
        AssetType.MOBILE_HOME,
    ],
    "Commercial": [
        AssetType.OFFICE,
        AssetType.RETAIL,
        AssetType.INDUSTRIAL,
    ],
    "Specialty": [
        AssetType.HOSPITALITY,
        AssetType.LAND,
        AssetType.MIXED_USE,
        AssetType.SPECIAL_USE,
    ],
}

# Typical acquisition strategies by asset type
ASSET_TYPE_STRATEGIES = {
    AssetType.SINGLE_FAMILY: ["wholesale", "flip", "hold", "partnership"],
    AssetType.MULTIFAMILY: ["hold", "flip", "partnership", "syndication"],
    AssetType.OFFICE: ["commercial", "creative_finance"],
    AssetType.LAND: ["arbitrage", "development"],
    AssetType.RETAIL: ["commercial", "hold"],
    AssetType.INDUSTRIAL: ["commercial", "hold"],
}

# Unit count ranges (for analysis)
ASSET_TYPE_UNIT_RANGES = {
    AssetType.SINGLE_FAMILY: (1, 4),
    AssetType.MULTIFAMILY: (5, 500),
    AssetType.OFFICE: None,
    AssetType.RETAIL: None,
    AssetType.INDUSTRIAL: None,
    AssetType.LAND: None,
    AssetType.MOBILE_HOME: (1, 1),
    AssetType.MIXED_USE: (1, 500),
    AssetType.SPECIAL_USE: None,
}


def get_launch_asset_types() -> list:
    """Asset types available at launch (V1)"""
    return [
        AssetType.SINGLE_FAMILY,
        AssetType.MULTIFAMILY,
        AssetType.LAND,
    ]


def get_future_asset_types() -> list:
    """Asset types designed for future expansion"""
    return [
        AssetType.OFFICE,
        AssetType.RETAIL,
        AssetType.INDUSTRIAL,
        AssetType.HOSPITALITY,
        AssetType.MOBILE_HOME,
        AssetType.MIXED_USE,
        AssetType.SPECIAL_USE,
    ]
