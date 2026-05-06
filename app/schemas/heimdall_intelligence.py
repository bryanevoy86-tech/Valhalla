"""
Heimdall Intelligence Layer - Pydantic Request/Response Schemas

This module defines all request and response schemas for the Heimdall Intelligence API.
These schemas provide type validation, documentation, and API contract enforcement.

Usage:
    from app.schemas.heimdall_intelligence import KnowledgeSourceCreate, KnowledgeSourceOut
    
    # In route handler:
    @router.post("/sources", response_model=KnowledgeSourceOut)
    async def create_source(source: KnowledgeSourceCreate):
        pass
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ============================================================================
# KNOWLEDGE SOURCES
# ============================================================================

class KnowledgeSourceCreate(BaseModel):
    """Request schema for creating a new knowledge source"""
    
    source_name: str = Field(
        ...,
        description="Human-readable name of the source",
        min_length=1,
        max_length=255,
        example="Memphis Market Report Q1 2026"
    )
    source_type: str = Field(
        ...,
        description="Type of source (government, public_web, forum, community, market_report, internal_outcome, operator_note, imported_doc)",
        example="market_report"
    )
    source_url: Optional[str] = Field(
        None,
        description="URL of the source if applicable",
        max_length=1024,
        example="https://example.com/report"
    )
    jurisdiction: Optional[str] = Field(
        None,
        description="Geographic jurisdiction (e.g., 'TN', 'US', 'GLOBAL')",
        max_length=10,
        example="TN"
    )
    market: Optional[str] = Field(
        None,
        description="Market code (e.g., 'memphis', 'nashville')",
        max_length=50,
        example="memphis"
    )
    category: Optional[str] = Field(
        None,
        description="Content category (e.g., 'market_trends', 'legal_constraints')",
        max_length=100,
        example="market_trends"
    )
    trust_level: str = Field(
        "medium",
        description="Trust level for this source (high, medium, low)",
        example="high"
    )
    active: bool = Field(
        True,
        description="Whether this source is currently active"
    )
    
    @validator("source_type")
    def validate_source_type(cls, v):
        """Validate source_type is recognized"""
        valid_types = [
            "government", "public_web", "forum", "community",
            "market_report", "internal_outcome", "operator_note", "imported_doc"
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"source_type must be one of: {valid_types}")
        return v.lower()
    
    @validator("trust_level")
    def validate_trust_level(cls, v):
        """Validate trust_level is recognized"""
        if v.lower() not in ["high", "medium", "low"]:
            raise ValueError("trust_level must be one of: high, medium, low")
        return v.lower()


class KnowledgeSourceOut(KnowledgeSourceCreate):
    """Response schema for knowledge source"""
    
    id: str = Field(..., description="Unique identifier for this source")
    created_at: datetime = Field(..., description="When this source was registered")
    updated_at: datetime = Field(..., description="Last update timestamp")
    knowledge_items_count: int = Field(0, description="Number of knowledge items from this source")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "source_name": "Memphis Market Report Q1 2026",
                "source_type": "market_report",
                "source_url": "https://example.com/report",
                "jurisdiction": "TN",
                "market": "memphis",
                "category": "market_trends",
                "trust_level": "high",
                "active": True,
                "created_at": "2026-04-13T10:30:00Z",
                "updated_at": "2026-04-13T10:30:00Z",
                "knowledge_items_count": 5
            }
        }


# ============================================================================
# KNOWLEDGE ITEMS
# ============================================================================

class KnowledgeItemCreate(BaseModel):
    """Request schema for ingesting a new knowledge item"""
    
    source_id: str = Field(
        ...,
        description="ID of the knowledge source this item comes from",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    title: str = Field(
        ...,
        description="Title of the knowledge item",
        min_length=1,
        max_length=500,
        example="Average Rehab Cost Q1 2026"
    )
    content_raw: str = Field(
        ...,
        description="Full raw content/text from the source",
        example="Full text from market report..."
    )
    content_summary: Optional[str] = Field(
        None,
        description="Short summary for quick reading",
        example="Bathroom rehabs $26-32k, kitchen $35-45k"
    )
    knowledge_type: str = Field(
        ...,
        description="Type of knowledge (rehab_cost, market_trend, negotiation_pattern, etc.)",
        example="rehab_cost"
    )
    market: Optional[str] = Field(
        None,
        description="Market this knowledge applies to",
        example="memphis"
    )
    strategy: Optional[List[str]] = Field(
        None,
        description="Strategies this knowledge applies to",
        example=["wholesale", "flip"]
    )
    asset_type: Optional[str] = Field(
        None,
        description="Asset type (single_family, multifamily, etc.)",
        example="single_family"
    )
    tags_json: Optional[List[str]] = Field(
        None,
        description="Free-form tags for categorization",
        example=["cost_driven", "seasonal", "labor_intensive"]
    )
    confidence_score: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Confidence this knowledge is accurate (0.0-1.0)",
        example=0.85
    )
    
    @validator("knowledge_type")
    def validate_knowledge_type(cls, v):
        """Validate knowledge_type is recognized"""
        valid_types = [
            "rehab_cost", "market_trend", "negotiation_pattern",
            "legal_constraint", "lead_source_pattern", "buyer_behavior",
            "seller_behavior", "rent_estimate", "arv_estimate",
            "financing_pattern", "tax_rule", "operational_rule"
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"knowledge_type must be one of: {valid_types}")
        return v.lower()


class KnowledgeItemOut(KnowledgeItemCreate):
    """Response schema for knowledge item"""
    
    id: str = Field(..., description="Unique identifier")
    status: str = Field(..., description="Status (draft, reviewed, trusted, deprecated, rejected)")
    created_at: datetime = Field(..., description="When ingested")
    updated_at: datetime = Field(..., description="Last updated")
    insights_count: int = Field(0, description="Number of insights extracted from this item")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "source_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Average Rehab Cost Q1 2026",
                "content_raw": "Full text...",
                "content_summary": "Bathroom rehabs $26-32k, kitchen $35-45k",
                "knowledge_type": "rehab_cost",
                "market": "memphis",
                "strategy": ["wholesale", "flip"],
                "asset_type": "single_family",
                "tags_json": ["cost_driven", "seasonal"],
                "confidence_score": 0.85,
                "status": "trusted",
                "created_at": "2026-04-13T11:00:00Z",
                "updated_at": "2026-04-13T11:00:00Z",
                "insights_count": 2
            }
        }


# ============================================================================
# KNOWLEDGE INSIGHTS
# ============================================================================

class KnowledgeInsightCreate(BaseModel):
    """Request schema for extracting a structured insight from a knowledge item"""
    
    insight_text: str = Field(
        ...,
        description="Human-readable insight",
        min_length=1,
        max_length=1000,
        example="For wholesale deals in Memphis, assume $28-32k bathroom rehab"
    )
    structured_value_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured data representation",
        example={"low": 28000, "high": 32000, "median": 30000}
    )
    applicable_market: Optional[str] = Field(
        None,
        description="Market this insight applies to",
        example="memphis"
    )
    applicable_strategy: Optional[str] = Field(
        None,
        description="Strategy this insight applies to",
        example="wholesale"
    )
    confidence_score: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="Confidence in this insight",
        example=0.90
    )


class KnowledgeInsightOut(KnowledgeInsightCreate):
    """Response schema for knowledge insight"""
    
    id: str = Field(..., description="Unique identifier")
    knowledge_item_id: str = Field(..., description="Parent knowledge item")
    supporting_evidence: Optional[str] = Field(None, description="Why we're confident")
    created_at: datetime = Field(..., description="When extracted")


# ============================================================================
# OUTCOME FEEDBACK
# ============================================================================

class OutcomeFeedbackCreate(BaseModel):
    """Request schema for recording outcome feedback"""
    
    case_id: Optional[str] = Field(
        None,
        description="Reference to execution case",
        example="CASE_123"
    )
    deal_id: Optional[str] = Field(
        None,
        description="Deal identifier",
        example="DEAL_2026_04_001"
    )
    market: str = Field(
        ...,
        description="Market where deal occurred",
        example="memphis"
    )
    strategy: str = Field(
        ...,
        description="Strategy used",
        example="wholesale"
    )
    asset_type: Optional[str] = Field(
        None,
        description="Asset type",
        example="single_family"
    )
    predicted_result_json: Optional[Dict[str, Any]] = Field(
        None,
        description="What was predicted",
        example={"estimated_arv": 185000, "estimated_rehab": 30000, "estimated_profit": 15000}
    )
    actual_result_json: Optional[Dict[str, Any]] = Field(
        None,
        description="What actually happened",
        example={"actual_arv": 188000, "actual_rehab": 35000, "actual_profit": 8000}
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the outcome"
    )


class OutcomeFeedbackOut(OutcomeFeedbackCreate):
    """Response schema for outcome feedback"""
    
    id: str = Field(..., description="Unique identifier")
    delta_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Calculated differences between predicted and actual"
    )
    lesson_text: Optional[str] = Field(None, description="Extracted lesson")
    confidence_adjustment: Optional[float] = Field(None, description="Confidence adjustment")
    created_at: datetime = Field(..., description="When recorded")


# ============================================================================
# DECISION MEMORY
# ============================================================================

class DecisionMemoryCreate(BaseModel):
    """Request schema for creating decision memory"""
    
    subject_type: str = Field(
        ...,
        description="What is being tracked",
        example="rehab_budget"
    )
    subject_id: Optional[str] = Field(
        None,
        description="Specific ID",
        example="memphis_wholesale_sf"
    )
    market: str = Field(..., description="Market context", example="memphis")
    strategy: Optional[str] = Field(None, description="Strategy context", example="wholesale")
    recommendation_text: str = Field(
        ...,
        description="What was recommended",
        example="Assume $30,000 budget"
    )
    decision_taken: Optional[str] = Field(
        None,
        description="What was actually decided"
    )
    outcome_score: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="How well it turned out"
    )
    lesson_text: Optional[str] = Field(None, description="What we learned")


class DecisionMemoryOut(DecisionMemoryCreate):
    """Response schema for decision memory"""
    
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="When recorded")
    updated_at: datetime = Field(..., description="Last updated")


# ============================================================================
# SEARCH & RECOMMENDATIONS
# ============================================================================

class KnowledgeSearchRequest(BaseModel):
    """Request schema for searching knowledge"""
    
    market: Optional[str] = Field(None, description="Filter by market")
    strategy: Optional[str] = Field(None, description="Filter by strategy")
    asset_type: Optional[str] = Field(None, description="Filter by asset type")
    knowledge_types: Optional[List[str]] = Field(
        None,
        description="Filter by knowledge types"
    )
    keywords: Optional[str] = Field(
        None,
        description="Free text search keywords"
    )
    min_confidence: float = Field(
        0.75,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    limit: int = Field(20, ge=1, le=100, description="Max results to return")


class SearchResultItem(BaseModel):
    """A single search result"""
    
    knowledge_item_id: str
    title: str
    content_summary: Optional[str]
    knowledge_type: str
    market: Optional[str]
    strategy: Optional[List[str]]
    confidence_score: float
    source_name: Optional[str]
    source_trust_level: Optional[str]
    insights_available: int
    relevance_score: float
    created_at: datetime


class KnowledgeSearchResponse(BaseModel):
    """Response schema for knowledge search"""
    
    query: Dict[str, Any]
    total_results: int
    results: List[SearchResultItem]


class InsightRecommendationRequest(BaseModel):
    """Request schema for insight recommendations"""
    
    market: str = Field(..., description="Market to get recommendation for")
    strategy: str = Field(..., description="Strategy to get recommendation for")
    asset_type: Optional[str] = Field(None, description="Asset type context")
    question: Optional[str] = Field(None, description="Natural language question")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class RecommendationEvidence(BaseModel):
    """Evidence supporting a recommendation"""
    
    text: str
    type: str  # "source", "outcome_feedback", "decision_memory"
    trust_level: Optional[str]
    relevance: float


class InsightRecommendationResponse(BaseModel):
    """Response schema for insight recommendation"""
    
    market: str
    strategy: str
    asset_type: Optional[str]
    question: Optional[str]
    recommendation: str
    confidence: float
    supporting_evidence: List[RecommendationEvidence]
    caveats: List[str]
    last_updated: Optional[str]
    advisory_only: bool = True


# ============================================================================
# MARKET MEMORY
# ============================================================================

class MarketMemoryInsight(BaseModel):
    """A single insight in market memory"""
    
    title: str
    value: str
    confidence: float
    last_updated: Optional[str]
    data_points: Optional[int]
    trend: Optional[str]


class MarketMemoryOutcome(BaseModel):
    """A recent outcome in market memory"""
    
    deal_date: str
    deal_id: Optional[str]
    profit_delta: Optional[float]
    profit_delta_pct: Optional[float]
    lesson: Optional[str]


class MarketMemorySummary(BaseModel):
    """Summary statistics for market memory"""
    
    total_knowledge_items: int
    total_outcomes_tracked: int
    overall_confidence: float
    knowledge_sources: int
    last_updated: str


class MarketMemorySnapshot(BaseModel):
    """Response schema for market memory snapshot"""
    
    market: str
    strategy: Optional[str]
    asset_type: Optional[str]
    generated_at: datetime
    primary_insights: List[MarketMemoryInsight]
    recent_outcomes: List[MarketMemoryOutcome]
    summary: MarketMemorySummary


# ============================================================================
# ERROR & STATUS RESPONSES
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    
    status: str = "error"
    status_code: int
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Health check response"""
    
    status: str = "healthy"
    service: str = "heimdall_intelligence"
    timestamp: datetime
    version: str = "1.0.0"
