# services/api/public_training/schema.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class PublicPropertyRecord:
    # Unified fields across provinces/cities
    source: str
    external_id: str  # stable key from source if possible
    province: str
    city: Optional[str]
    address: Optional[str]

    assessed_value: Optional[float]
    assessment_year: Optional[int]

    # Optional fields (vary by source)
    property_type: Optional[str]
    year_built: Optional[int]
    land_area: Optional[float]
    building_area: Optional[float]

    # Synthetic fields we compute later
    synthetic_risk_level: Optional[str] = None
    synthetic_should_pursue: Optional[bool] = None
    synthetic_offer_low: Optional[float] = None
    synthetic_offer_high: Optional[float] = None
    synthetic_human_review_required: Optional[bool] = None
    synthetic_confidence: Optional[float] = None
