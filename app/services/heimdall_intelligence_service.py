"""
Heimdall Intelligence Service Layer

This module contains the business logic for the Heimdall Intelligence Layer.
It handles knowledge ingestion, searching, recommendations, outcome tracking, and learning.

IMPORTANT: This is Phase 1 with stubbed implementations. Future phases will add:
- Database persistence (currently stubbed)
- LLM integration for insight extraction
- Advanced recommendation algorithms
- Outcome delta calculation and lesson generation

Usage:
    service = HeimdallIntelligenceService()
    source = service.register_source(...)
    item = service.ingest_knowledge_item(...)
    insights = service.search_knowledge(...)
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class HeimdallIntelligenceService:
    """
    Main service for Heimdall Intelligence Layer V1.
    
    Handles all business logic for knowledge management and outcome tracking.
    Phase 1: In-memory and stubbed database operations.
    Phase 2: Will integrate with SQLAlchemy ORM for persistence.
    """
    
    def __init__(self):
        """Initialize the service with optional in-memory storage"""
        # Phase 1: In-memory storage for beta testing
        # Phase 2: Will be replaced with database queries
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.knowledge_items: Dict[str, Dict[str, Any]] = {}
        self.insights: Dict[str, Dict[str, Any]] = {}
        self.outcomes: Dict[str, Dict[str, Any]] = {}
        self.decisions: Dict[str, Dict[str, Any]] = {}
        
        # ID counters (Phase 1 only)
        self._source_counter = 0
        self._item_counter = 0
        self._insight_counter = 0
        self._outcome_counter = 0
        self._decision_counter = 0
    
    # ========================================================================
    # KNOWLEDGE SOURCES
    # ========================================================================
    
    def register_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new knowledge source.
        
        Args:
            source_data: Source information (name, type, url, trust_level, etc.)
        
        Returns:
            Created source record with ID
        
        TODO: Phase 2 - persist to database via SQLAlchemy
        """
        logger.info(f"Registering source: {source_data.get('source_name')}")
        
        # Generate ID (Phase 1 only)
        self._source_counter += 1
        source_id = f"src_{self._source_counter:06d}"
        
        # Create source record
        source_record = {
            "id": source_id,
            **source_data,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "knowledge_items_count": 0,
        }
        
        # Store (Phase 1: in-memory, Phase 2: database)
        self.sources[source_id] = source_record
        logger.info(f"Source registered: {source_id}")
        
        return source_record
    
    def get_sources(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List all knowledge sources with optional filtering.
        
        Args:
            filters: Optional filter dict (market, trust_level, active, etc.)
        
        Returns:
            List of source records
        
        TODO: Phase 2 - query database with filters
        """
        logger.debug("Listing sources")
        
        sources = list(self.sources.values())
        
        # Apply filters
        if filters:
            if "market" in filters:
                sources = [s for s in sources if s.get("market") == filters["market"]]
            if "trust_level" in filters:
                sources = [s for s in sources if s.get("trust_level") == filters["trust_level"]]
            if "active" in filters:
                sources = [s for s in sources if s.get("active") == filters["active"]]
        
        return sources
    
    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get a single source by ID"""
        return self.sources.get(source_id)
    
    # ========================================================================
    # KNOWLEDGE ITEMS
    # ========================================================================
    
    def ingest_knowledge_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a new piece of knowledge.
        
        Args:
            item_data: Knowledge item data (title, content_raw, content_summary, etc.)
        
        Returns:
            Created knowledge item record
        
        TODO: Phase 2 - persist to database
        TODO: Phase 2+ - optionally call LLM to generate content_summary if missing
        """
        logger.info(f"Ingesting knowledge: {item_data.get('title')}")
        
        # Verify source exists
        source_id = item_data.get("source_id")
        if source_id not in self.sources:
            raise ValueError(f"Source {source_id} not found")
        
        # Generate ID (Phase 1 only)
        self._item_counter += 1
        item_id = f"item_{self._item_counter:06d}"
        
        # Create item record
        item_record = {
            "id": item_id,
            **item_data,
            "status": "draft",  # Always start as draft
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "insights_count": 0,
        }
        
        # If content_summary is missing and content_raw exists, summarize
        if not item_record.get("content_summary") and item_record.get("content_raw"):
            # TODO: Phase 2+ - call LLM to generate summary
            # For now, use first 200 chars of raw content
            item_record["content_summary"] = item_record["content_raw"][:200] + "..."
        
        # Store
        self.knowledge_items[item_id] = item_record
        
        # Update source counter
        if source_id in self.sources:
            self.sources[source_id]["knowledge_items_count"] += 1
        
        logger.info(f"Knowledge item ingested: {item_id}")
        return item_record
    
    def get_knowledge_items(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List knowledge items with optional filtering.
        
        Args:
            filters: Optional filters (source_id, market, strategy, asset_type, status, etc.)
        
        Returns:
            List of knowledge items
        
        TODO: Phase 2 - query database with filters
        """
        logger.debug("Listing knowledge items")
        
        items = list(self.knowledge_items.values())
        
        # Apply filters
        if filters:
            if "source_id" in filters:
                items = [i for i in items if i.get("source_id") == filters["source_id"]]
            if "market" in filters:
                items = [i for i in items if i.get("market") == filters["market"]]
            if "strategy" in filters:
                strategy = filters["strategy"]
                items = [i for i in items if strategy in (i.get("strategy") or [])]
            if "knowledge_type" in filters:
                items = [i for i in items if i.get("knowledge_type") == filters["knowledge_type"]]
            if "status" in filters:
                items = [i for i in items if i.get("status") == filters["status"]]
            if "min_confidence" in filters:
                min_conf = filters["min_confidence"]
                items = [i for i in items if (i.get("confidence_score") or 0) >= min_conf]
        
        return items
    
    def get_knowledge_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a single knowledge item by ID"""
        return self.knowledge_items.get(item_id)
    
    def update_knowledge_item_status(self, item_id: str, new_status: str) -> Dict[str, Any]:
        """Update the status of a knowledge item (draft→reviewed→trusted, etc.)"""
        if item_id not in self.knowledge_items:
            raise ValueError(f"Item {item_id} not found")
        
        item = self.knowledge_items[item_id]
        item["status"] = new_status
        item["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated item {item_id} status to {new_status}")
        return item
    
    # ========================================================================
    # KNOWLEDGE INSIGHTS
    # ========================================================================
    
    def extract_structured_insight(self, insight_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and store a structured insight from a knowledge item.
        
        Args:
            insight_data: Insight (text, structured_value_json, applicable_market, etc.)
        
        Returns:
            Created insight record
        
        TODO: Phase 2+ - LLM integration to auto-extract structured_value_json
        """
        logger.info(f"Extracting insight from item")
        
        # Verify knowledge item exists
        item_id = insight_data.get("knowledge_item_id")
        if item_id not in self.knowledge_items:
            raise ValueError(f"Knowledge item {item_id} not found")
        
        # Generate ID
        self._insight_counter += 1
        insight_id = f"insight_{self._insight_counter:06d}"
        
        # Create insight record
        insight_record = {
            "id": insight_id,
            **insight_data,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store
        self.insights[insight_id] = insight_record
        
        # Update item counter
        if item_id in self.knowledge_items:
            self.knowledge_items[item_id]["insights_count"] += 1
        
        logger.info(f"Insight extracted: {insight_id}")
        return insight_record
    
    def get_insights_for_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all insights for a specific knowledge item"""
        return [i for i in self.insights.values() if i.get("knowledge_item_id") == item_id]
    
    # ========================================================================
    # SEARCH
    # ========================================================================
    
    def search_knowledge(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search knowledge base for relevant items.
        
        Args:
            search_params: Search parameters (market, strategy, keywords, confidence, etc.)
        
        Returns:
            Search results with matching items
        
        TODO: Phase 2+ - add full-text search, semantic search, relevance scoring
        """
        logger.info(f"Searching knowledge with params: {search_params}")
        
        # Get base set of items
        filters = {}
        if "market" in search_params:
            filters["market"] = search_params["market"]
        if "strategy" in search_params:
            filters["strategy"] = search_params["strategy"]
        if "knowledge_type" in search_params:
            filters["knowledge_type"] = search_params["knowledge_type"]
        if "min_confidence" in search_params:
            filters["min_confidence"] = search_params["min_confidence"]
        
        items = self.get_knowledge_items(filters)
        
        # Apply keyword search if provided
        keywords = search_params.get("keywords", "").lower()
        if keywords:
            items = [
                i for i in items
                if keywords in i.get("title", "").lower()
                or keywords in i.get("content_summary", "").lower()
            ]
        
        # Build result items with relevance scoring
        results = []
        for item in items:
            # TODO: Phase 2+ - calculate real relevance scores
            relevance_score = item.get("confidence_score", 0.5)
            
            result_item = {
                "knowledge_item_id": item["id"],
                "title": item.get("title"),
                "content_summary": item.get("content_summary"),
                "knowledge_type": item.get("knowledge_type"),
                "market": item.get("market"),
                "strategy": item.get("strategy"),
                "confidence_score": item.get("confidence_score", 0.5),
                "source_name": self.sources.get(item.get("source_id"), {}).get("source_name"),
                "source_trust_level": self.sources.get(item.get("source_id"), {}).get("trust_level"),
                "insights_available": item.get("insights_count", 0),
                "relevance_score": relevance_score,
                "created_at": item.get("created_at"),
            }
            results.append(result_item)
        
        # Limit results
        limit = search_params.get("limit", 20)
        results = results[:limit]
        
        return {
            "query": search_params,
            "total_results": len(results),
            "results": results,
        }
    
    # ========================================================================
    # RECOMMENDATIONS
    # ========================================================================
    
    def get_recommendations(self, rec_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get data-backed recommendations for a market/strategy context.
        
        Args:
            rec_params: Request parameters (market, strategy, asset_type, question, etc.)
        
        Returns:
            Recommendation with supporting evidence and confidence
        
        TODO: Phase 2+ - LLM integration for recommendation synthesis
        TODO: Phase 2+ - advanced recommendation ranking algorithms
        """
        logger.info(f"Getting recommendations for: {rec_params}")
        
        market = rec_params.get("market")
        strategy = rec_params.get("strategy")
        
        # Find relevant insights
        search_params = {
            "market": market,
            "strategy": strategy,
            "min_confidence": 0.5,
        }
        search_result = self.search_knowledge(search_params)
        
        # If no results, return empty recommendation
        if not search_result["results"]:
            return {
                "market": market,
                "strategy": strategy,
                "recommendation": "No knowledge available for this market/strategy combination",
                "confidence": 0.0,
                "supporting_evidence": [],
                "caveats": ["No baseline data available yet"],
                "advisory_only": True,
            }
        
        # Aggregate evidence
        evidence = []
        avg_confidence = 0.0
        
        for result in search_result["results"]:
            evidence.append({
                "text": result["title"],
                "type": "knowledge_item",
                "trust_level": result.get("source_trust_level"),
                "relevance": result.get("relevance_score", 0.5),
            })
            avg_confidence += result.get("confidence_score", 0.5)
        
        avg_confidence = avg_confidence / len(evidence) if evidence else 0.0
        
        # TODO: Phase 2+ - compile human-friendly recommendation from insights
        recommendation_text = f"Based on {len(evidence)} sources, general guidance available"
        
        return {
            "market": market,
            "strategy": strategy,
            "asset_type": rec_params.get("asset_type"),
            "question": rec_params.get("question"),
            "recommendation": recommendation_text,
            "confidence": min(avg_confidence, 0.95),  # Cap at 0.95
            "supporting_evidence": evidence,
            "caveats": [
                "Recommendation is based on available knowledge sources",
                "Verify with current market conditions",
                "This is advisory only - human judgment required",
            ],
            "last_updated": datetime.utcnow().isoformat(),
            "advisory_only": True,
        }
    
    # ========================================================================
    # OUTCOME FEEDBACK & LEARNING
    # ========================================================================
    
    def record_outcome_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record actual vs. predicted outcome for learning.
        
        Args:
            feedback_data: Outcome data (case_id, market, strategy, predicted, actual, etc.)
        
        Returns:
            Created outcome feedback record
        
        TODO: Phase 2 - calculate delta_json automatically
        """
        logger.info(f"Recording outcome feedback for {feedback_data.get('deal_id')}")
        
        # Generate ID
        self._outcome_counter += 1
        outcome_id = f"outcome_{self._outcome_counter:06d}"
        
        # Calculate delta if both predicted and actual are provided
        delta_json = None
        if feedback_data.get("predicted_result_json") and feedback_data.get("actual_result_json"):
            delta_json = self._calculate_delta(
                feedback_data["predicted_result_json"],
                feedback_data["actual_result_json"]
            )
        
        # Create record
        outcome_record = {
            "id": outcome_id,
            **feedback_data,
            "delta_json": delta_json,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Store
        self.outcomes[outcome_id] = outcome_record
        
        logger.info(f"Outcome feedback recorded: {outcome_id}")
        return outcome_record
    
    def _calculate_delta(self, predicted: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate differences between predicted and actual values.
        
        TODO: Phase 2+ - smarter delta calculation, percentage calculations, etc.
        """
        delta = {}
        
        # For now, simple numeric comparisons
        for key in predicted:
            if key in actual and isinstance(predicted[key], (int, float)) and isinstance(actual[key], (int, float)):
                diff = actual[key] - predicted[key]
                delta[f"{key}_delta"] = diff
                if predicted[key] != 0:
                    pct_diff = (diff / predicted[key]) * 100
                    delta[f"{key}_delta_pct"] = round(pct_diff / 100, 4)  # As decimal
        
        return delta
    
    def generate_lesson(self, outcome_id: str, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate and store lesson from outcome feedback.
        
        Args:
            outcome_id: ID of the outcome feedback
            lesson_data: Lesson information
        
        Returns:
            Updated outcome record with lesson
        
        TODO: Phase 2+ - LLM integration to auto-generate lessons from delta
        """
        logger.info(f"Generating lesson for outcome {outcome_id}")
        
        if outcome_id not in self.outcomes:
            raise ValueError(f"Outcome {outcome_id} not found")
        
        outcome = self.outcomes[outcome_id]
        outcome["lesson_text"] = lesson_data.get("lesson_text")
        outcome["confidence_adjustment"] = lesson_data.get("confidence_adjustment", 0.0)
        outcome["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Lesson recorded for outcome {outcome_id}")
        return outcome
    
    # ========================================================================
    # MARKET MEMORY
    # ========================================================================
    
    def build_market_memory_snapshot(self, market: str, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Build a snapshot of market memory with current insights and performance.
        
        Args:
            market: Market to build snapshot for
            strategy: Optional strategy to filter by
        
        Returns:
            Market memory snapshot with insights, outcomes, and summary
        
        TODO: Phase 2+ - advanced aggregation, trend analysis, confidence recalc
        """
        logger.info(f"Building market memory for {market}")
        
        # Get relevant insights
        search_params = {"market": market}
        if strategy:
            search_params["strategy"] = strategy
        search_result = self.search_knowledge(search_params)
        
        primary_insights = []
        for result in search_result["results"]:
            insight = {
                "title": result["title"],
                "value": result.get("content_summary", "N/A"),
                "confidence": result.get("confidence_score", 0.5),
                "last_updated": result.get("created_at"),
                "data_points": result.get("insights_available", 0),
            }
            primary_insights.append(insight)
        
        # Get recent outcomes
        recent_filter = {
            "market": market,
        }
        if strategy:
            recent_filter["strategy"] = strategy
        
        outcomes = [
            o for o in self.outcomes.values()
            if o.get("market") == market and (not strategy or o.get("strategy") == strategy)
        ]
        
        # Sort by date desc and take last N
        outcomes = sorted(
            outcomes,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:10]
        
        recent_outcomes = []
        for outcome in outcomes:
            outcome_item = {
                "deal_date": outcome.get("created_at", "").split("T")[0],
                "deal_id": outcome.get("deal_id"),
                "profit_delta": None,
                "profit_delta_pct": None,
                "lesson": outcome.get("lesson_text"),
            }
            
            # Try to extract profit delta
            if outcome.get("delta_json:").get("actual_profit_delta"):
                outcome_item["profit_delta"] = outcome["delta_json"]["actual_profit_delta"]
            
            recent_outcomes.append(outcome_item)
        
        # Summary
        summary = {
            "total_knowledge_items": len(search_result["results"]),
            "total_outcomes_tracked": len(outcomes),
            "overall_confidence": sum(i["confidence"] for i in primary_insights) / max(len(primary_insights), 1),
            "knowledge_sources": len(set(i.get("source_name") for i in search_result["results"])),
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        return {
            "market": market,
            "strategy": strategy,
            "generated_at": datetime.utcnow().isoformat(),
            "primary_insights": primary_insights,
            "recent_outcomes": recent_outcomes,
            "summary": summary,
        }
    
    # ========================================================================
    # DECISION MEMORY
    # ========================================================================
    
    def record_decision_memory(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a decision and its context for future learning.
        
        Args:
            decision_data: Decision information
        
        Returns:
            Created decision memory record
        """
        logger.info(f"Recording decision: {decision_data.get('subject_type')}")
        
        # Generate ID
        self._decision_counter += 1
        decision_id = f"decision_{self._decision_counter:06d}"
        
        # Create record
        decision_record = {
            "id": decision_id,
            **decision_data,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Store
        self.decisions[decision_id] = decision_record
        
        logger.info(f"Decision memory recorded: {decision_id}")
        return decision_record
    
    def get_decision_memory(self, market: str, strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get decision memory for a market/strategy"""
        decisions = [
            d for d in self.decisions.values()
            if d.get("market") == market and (not strategy or d.get("strategy") == strategy)
        ]
        return decisions


# Singleton instance for use across the application
_service_instance: Optional[HeimdallIntelligenceService] = None


def get_service() -> HeimdallIntelligenceService:
    """
    Get or create the service instance.
    
    This is a simple singleton pattern for Phase 1.
    Phase 2 will use dependency injection with FastAPI.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = HeimdallIntelligenceService()
    return _service_instance
