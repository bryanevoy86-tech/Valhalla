"""
Heimdall Intelligence Layer - FastAPI Router

This router defines all endpoints for the Heimdall Intelligence V1 API.
All endpoints are prefixed with /heimdall/intelligence and are completely isolated
from the execution layer.

The router is designed to be:
- Imported and registered cleanly in the main app
- Non-breaking (can be disabled without affecting execution routes)
- Self-contained (no dependencies on execution layer)

Usage (in main app):
    from app.routers.heimdall_intelligence import router as heimdall_router
    app.include_router(heimdall_router)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
import logging

from app.services.heimdall_intelligence_service import get_service, HeimdallIntelligenceService
from app.schemas.heimdall_intelligence import (
    # Sources
    KnowledgeSourceCreate,
    KnowledgeSourceOut,
    # Items
    KnowledgeItemCreate,
    KnowledgeItemOut,
    # Insights
    KnowledgeInsightCreate,
    KnowledgeInsightOut,
    # Outcomes
    OutcomeFeedbackCreate,
    OutcomeFeedbackOut,
    # Decisions
    DecisionMemoryCreate,
    DecisionMemoryOut,
    # Search & Recommendations
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    InsightRecommendationRequest,
    InsightRecommendationResponse,
    # Market Memory
    MarketMemorySnapshot,
    # Error
    ErrorResponse,
    HealthCheckResponse,
)

logger = logging.getLogger(__name__)

# Create router with unique prefix
router = APIRouter(
    prefix="/heimdall/intelligence",
    tags=["Heimdall Intelligence"],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for Heimdall Intelligence Layer"""
    return HealthCheckResponse(timestamp=get_service().__class__.__dict__)


# ============================================================================
# KNOWLEDGE SOURCES
# ============================================================================

@router.post(
    "/sources",
    response_model=KnowledgeSourceOut,
    status_code=201,
    summary="Register a new knowledge source",
    description="Register a knowledge source (e.g., market report, forum, government data)"
)
async def create_knowledge_source(
    source: KnowledgeSourceCreate,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """
    Register a new knowledge source.
    
    Knowledge sources are where knowledge comes from (trust level, type, categorization).
    Each knowledge item must reference a source.
    """
    try:
        result = service.register_source(source.dict())
        return result
    except ValueError as e:
        logger.error(f"Validation error registering source: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering source: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/sources",
    response_model=List[KnowledgeSourceOut],
    summary="List knowledge sources",
    description="List all registered knowledge sources with optional filtering"
)
async def list_knowledge_sources(
    market: Optional[str] = Query(None, description="Filter by market"),
    trust_level: Optional[str] = Query(None, description="Filter by trust level (high, medium, low)"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """List all registered knowledge sources"""
    try:
        filters = {}
        if market:
            filters["market"] = market
        if trust_level:
            filters["trust_level"] = trust_level
        if active is not None:
            filters["active"] = active
        
        sources = service.get_sources(filters)
        return sources[offset:offset + limit]
    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# KNOWLEDGE ITEMS
# ============================================================================

@router.post(
    "/items",
    response_model=KnowledgeItemOut,
    status_code=201,
    summary="Ingest a knowledge item",
    description="Ingest a new piece of knowledge from a source"
)
async def create_knowledge_item(
    item: KnowledgeItemCreate,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """
    Ingest a new knowledge item.
    
    Knowledge items are individual pieces of knowledge that can be searched,
    indexed, and used to generate recommendations.
    """
    try:
        result = service.ingest_knowledge_item(item.dict())
        return result
    except ValueError as e:
        logger.error(f"Validation error ingesting item: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error ingesting item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/items",
    response_model=List[KnowledgeItemOut],
    summary="List knowledge items",
    description="List knowledge items with optional filtering"
)
async def list_knowledge_items(
    source_id: Optional[str] = Query(None, description="Filter by source"),
    market: Optional[str] = Query(None, description="Filter by market"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    knowledge_type: Optional[str] = Query(None, description="Filter by knowledge type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """List knowledge items"""
    try:
        filters = {}
        if source_id:
            filters["source_id"] = source_id
        if market:
            filters["market"] = market
        if strategy:
            filters["strategy"] = strategy
        if knowledge_type:
            filters["knowledge_type"] = knowledge_type
        if status:
            filters["status"] = status
        if min_confidence > 0.0:
            filters["min_confidence"] = min_confidence
        
        items = service.get_knowledge_items(filters)
        return items[offset:offset + limit]
    except Exception as e:
        logger.error(f"Error listing items: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/items/{item_id}",
    response_model=KnowledgeItemOut,
    summary="Get a knowledge item",
    description="Retrieve full details of a single knowledge item"
)
async def get_knowledge_item(
    item_id: str,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """Get a specific knowledge item"""
    try:
        item = service.get_knowledge_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# KNOWLEDGE INSIGHTS
# ============================================================================

@router.post(
    "/items/{item_id}/insights",
    response_model=KnowledgeInsightOut,
    status_code=201,
    summary="Extract a structured insight",
    description="Extract a structured, actionable insight from a knowledge item"
)
async def create_insight(
    item_id: str,
    insight: KnowledgeInsightCreate,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """Extract a structured insight from a knowledge item"""
    try:
        insight_data = insight.dict()
        insight_data["knowledge_item_id"] = item_id
        result = service.extract_structured_insight(insight_data)
        return result
    except ValueError as e:
        logger.error(f"Validation error creating insight: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating insight: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/items/{item_id}/insights",
    response_model=List[KnowledgeInsightOut],
    summary="Get insights for an item",
    description="List all insights extracted from a knowledge item"
)
async def get_item_insights(
    item_id: str,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """Get all insights for a knowledge item"""
    try:
        # Verify item exists
        if not service.get_knowledge_item(item_id):
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        insights = service.get_insights_for_item(item_id)
        return insights
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# SEARCH
# ============================================================================

@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search knowledge base",
    description="Search knowledge items by market, strategy, keywords, etc."
)
async def search_knowledge(
    search_req: KnowledgeSearchRequest,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """
    Search the knowledge base.
    
    Returns relevant knowledge items with matching criteria, confidence scores,
    and relevance rankings.
    """
    try:
        result = service.search_knowledge(search_req.dict())
        return result
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

@router.post(
    "/recommend",
    response_model=InsightRecommendationResponse,
    summary="Get recommendations",
    description="Get data-backed recommendations for market/strategy context"
)
async def get_recommendations(
    rec_req: InsightRecommendationRequest,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """
    Get recommendations based on available knowledge.
    
    Returns data-backed recommendations with supporting evidence,
    confidence scores, and caveats.
    
    IMPORTANT: These are advisory only. Human judgment required.
    """
    try:
        result = service.get_recommendations(rec_req.dict())
        return result
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# OUTCOME FEEDBACK
# ============================================================================

@router.post(
    "/outcomes",
    response_model=OutcomeFeedbackOut,
    status_code=201,
    summary="Record outcome feedback",
    description="Record actual vs predicted outcome for learning"
)
async def record_outcome(
    outcome: OutcomeFeedbackCreate,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """
    Record outcome feedback from an executed deal.
    
    This feeds the learning loop - comparing predictions to actual results
    and extracting lessons for future improvements.
    """
    try:
        result = service.record_outcome_feedback(outcome.dict())
        return result
    except ValueError as e:
        logger.error(f"Validation error recording outcome: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error recording outcome: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/outcomes",
    response_model=List[OutcomeFeedbackOut],
    summary="List outcome feedback",
    description="List recorded outcome feedback with optional filtering"
)
async def list_outcomes(
    market: Optional[str] = Query(None, description="Filter by market"),
    strategy: Optional[str] = Query(None, description="Filter by strategy"),
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """List recorded outcome feedback"""
    try:
        # This would be implemented via database query in Phase 2
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error listing outcomes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/outcomes/{outcome_id}/lesson",
    response_model=OutcomeFeedbackOut,
    summary="Generate lesson from outcome",
    description="Extract and store lesson from outcome feedback"
)
async def generate_lesson(
    outcome_id: str,
    lesson_data: dict,
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """Generate and store lesson from outcome"""
    try:
        result = service.generate_lesson(outcome_id, lesson_data)
        return result
    except ValueError as e:
        logger.error(f"Validation error generating lesson: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating lesson: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# MARKET MEMORY
# ============================================================================

@router.get(
    "/market-memory",
    response_model=MarketMemorySnapshot,
    summary="Get market memory snapshot",
    description="Get aggregated insights and performance for a market/strategy"
)
async def get_market_memory(
    market: str = Query(..., description="Market name"),
    strategy: Optional[str] = Query(None, description="Optional strategy filter"),
    service: HeimdallIntelligenceService = Depends(get_service)
):
    """
    Get a market memory snapshot.
    
    Returns aggregated insights, recent outcomes, and performance metrics
    for a given market and optional strategy combination.
    """
    try:
        result = service.build_market_memory_snapshot(market, strategy)
        return result
    except Exception as e:
        logger.error(f"Error building market memory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# ERROR HANDLERS (Optional - can be global)
# ============================================================================

@router.get(
    "/debug/stats",
    summary="Debug: Service statistics",
    description="Return in-memory storage statistics (Phase 1 only)"
)
async def debug_stats(service: HeimdallIntelligenceService = Depends(get_service)):
    """
    Debug endpoint showing current service statistics.
    
    REMOVE in production.
    Phase 1 only for testing.
    """
    return {
        "sources_count": len(service.sources),
        "items_count": len(service.knowledge_items),
        "insights_count": len(service.insights),
        "outcomes_count": len(service.outcomes),
        "decisions_count": len(service.decisions),
    }
