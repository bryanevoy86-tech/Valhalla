"""
Routing Service - routes opportunity to appropriate execution pipeline
"""
from typing import Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionPipeline(str, Enum):
    """Available execution pipelines"""
    QUICK_WHOLESALE = "quick_wholesale"
    STANDARD_WHOLESALE = "standard_wholesale"
    FIX_AND_FLIP = "fix_and_flip"
    BUY_AND_HOLD = "buy_and_hold"
    PARTNERSHIP = "partnership"
    BUSINESS_JV = "business_jv"
    MANUAL_REVIEW = "manual_review"
    BLOCKED = "blocked"


class RoutingService:
    """
    Routes opportunities to execution pipelines based on:
    - Classification (real_estate, business, arbitrage, jv)
    - Assessment (profit, confidence, risk)
    - Market conditions (coming in V2)
    """
    
    def __init__(self):
        """Initialize routing rules"""
        self.rules = self._build_routing_rules()
    
    def _build_routing_rules(self) -> dict:
        """Build routing rules configuration"""
        # Rules are encoded in the scoring logic
        # This returns an empty dict for now (rules are implicit in _score_pipeline_fit)
        return {}
    
    def route(
        self,
        classification: str,
        assessment: dict,
        extracted_fields: dict,
    ) -> Dict[str, Any]:
        """
        Route opportunity to pipeline.
        
        Returns: {
            "pipeline": ExecutionPipeline,
            "confidence": float,
            "reasoning": str,
            "required_verifications": [list],
            "estimated_timeline_days": int,
            "estimated_effort_level": str,  # low, medium, high
        }
        """
        
        # Get default pipeline for classification
        default_pipeline = self._get_default_pipeline(classification)
        
        # Score fit to each possible pipeline
        scores = {}
        for pipeline in ExecutionPipeline:
            score = self._score_pipeline_fit(
                pipeline=pipeline,
                classification=classification,
                assessment=assessment,
                extracted_fields=extracted_fields,
            )
            scores[pipeline] = score
        
        # Select best pipeline
        best_pipeline = max(scores, key=scores.get)
        confidence = scores[best_pipeline]
        
        # Block if blocked
        if best_pipeline == ExecutionPipeline.BLOCKED:
            return {
                "pipeline": "blocked",
                "confidence": 100,
                "reasoning": assessment.get("reason", "Deal blocked for safety reasons"),
                "required_verifications": [],
                "estimated_timeline_days": 0,
                "estimated_effort_level": "n/a",
            }
        
        # Manual review if confidence too low
        if confidence < 40:
            return {
                "pipeline": "manual_review",
                "confidence": confidence,
                "reasoning": "Insufficient data for automated routing - manual review required",
                "required_verifications": self._get_required_verifications(classification),
                "estimated_timeline_days": 2,
                "estimated_effort_level": "high",
            }
        
        # Get details for best pipeline
        details = self._get_pipeline_details(best_pipeline, assessment)
        
        return {
            "pipeline": best_pipeline.value,
            "confidence": min(100, max(0, confidence)),
            "reasoning": details.get("reasoning"),
            "required_verifications": details.get("verifications", []),
            "estimated_timeline_days": details.get("timeline_days", 14),
            "estimated_effort_level": details.get("effort_level", "medium"),
        }
    
    def _score_pipeline_fit(
        self,
        pipeline: ExecutionPipeline,
        classification: str,
        assessment: dict,
        extracted_fields: dict,
    ) -> float:
        """Score 0-100 on how well opportunity fits pipeline"""
        
        # Blocked deals score 0 for all non-blocked pipelines
        if assessment.get("blocked", False):
            return 100 if pipeline == ExecutionPipeline.BLOCKED else 0
        
        profit = assessment.get("estimated_profit", 0)
        confidence = assessment.get("confidence_score", 50)
        risk = assessment.get("risk_score", 50)
        arv = assessment.get("estimated_value", 0)
        
        # Route by classification AND financial metrics
        if classification == "real_estate":
            if pipeline == ExecutionPipeline.QUICK_WHOLESALE:
                # High profit, low work needed, tight timeline
                score = 0
                if profit > 20000:
                    score += 30
                if assessment.get("estimated_repair_cost", 0) < 5000:
                    score += 30
                if confidence > 70:
                    score += 20
                if risk < 30:
                    score += 20
                return score
            
            elif pipeline == ExecutionPipeline.STANDARD_WHOLESALE:
                # Medium profit, moderate confidence
                score = 0
                if 10000 < profit < 50000:
                    score += 40
                if 40 < confidence < 85:
                    score += 30
                if 25 < risk < 60:
                    score += 30
                return score
            
            elif pipeline == ExecutionPipeline.FIX_AND_FLIP:
                # Medium-high profit, significant repairs, good ARV
                score = 0
                if profit > 25000:
                    score += 30
                if 10000 < assessment.get("estimated_repair_cost", 0) < 75000:
                    score += 35
                if confidence > 60:
                    score += 20
                if arv > 250000:
                    score += 15
                return score
            
            elif pipeline == ExecutionPipeline.BUY_AND_HOLD:
                # Positive cash flow, lower profit, long-term
                score = 0
                if 0 < profit < 20000:
                    score += 25
                if confidence > 65:
                    score += 30
                if risk < 40:
                    score += 30
                if extracted_fields.get("bedrooms") and extracted_fields.get("bedrooms") >= 2:
                    score += 15
                return score
            
            else:
                return 0
        
        elif classification == "business":
            if pipeline == ExecutionPipeline.BUSINESS_JV:
                # Default for businesses
                if confidence > 40:
                    return 60
                else:
                    return 0
            elif pipeline == ExecutionPipeline.PARTNERSHIP:
                # Alternative for businesses
                if confidence > 50:
                    return 50
                else:
                    return 0
            else:
                return 0
        
        elif classification == "jv":
            if pipeline == ExecutionPipeline.PARTNERSHIP:
                return min(100, confidence + 20)
            else:
                return 0
        
        else:  # arbitrage or unknown
            if pipeline == ExecutionPipeline.MANUAL_REVIEW:
                return 50
            else:
                return 0
    
    def _get_default_pipeline(self, classification: str) -> ExecutionPipeline:
        """Get default pipeline for classification"""
        defaults = {
            "real_estate": ExecutionPipeline.STANDARD_WHOLESALE,
            "business": ExecutionPipeline.BUSINESS_JV,
            "arbitrage": ExecutionPipeline.QUICK_WHOLESALE,
            "jv": ExecutionPipeline.PARTNERSHIP,
            "unknown": ExecutionPipeline.MANUAL_REVIEW,
        }
        return defaults.get(classification, ExecutionPipeline.MANUAL_REVIEW)
    
    def _get_pipeline_details(self, pipeline: ExecutionPipeline, assessment: dict) -> dict:
        """Get execution details for pipeline"""
        
        details = {
            ExecutionPipeline.QUICK_WHOLESALE: {
                "reasoning": "High-profit, minimal-repair opportunity - execute wholesale quickly",
                "verifications": ["Title verification", "Seller motivation confirmation"],
                "timeline_days": 7,
                "effort_level": "low",
                "next_steps": [
                    "Contact seller to confirm motivation",
                    "Get comparable sales for market validation",
                    "Generate LOI if interested",
                ],
            },
            ExecutionPipeline.STANDARD_WHOLESALE: {
                "reasoning": "Good wholesale opportunity with moderate timeline",
                "verifications": ["Title search", "Property inspection", "Comparables pull"],
                "timeline_days": 14,
                "effort_level": "medium",
                "next_steps": [
                    "Schedule property inspection",
                    "Pull recent comps in area",
                    "Verify seller authority",
                ],
            },
            ExecutionPipeline.FIX_AND_FLIP: {
                "reasoning": "Value-add opportunity suitable for renovation project",
                "verifications": ["Detailed inspection", "Contractor quote", "After-repair comparables"],
                "timeline_days": 30,
                "effort_level": "high",
                "next_steps": [
                    "Get detailed contractor estimate",
                    "Calculate ARV with comps",
                    "Evaluate financing options",
                ],
            },
            ExecutionPipeline.BUY_AND_HOLD: {
                "reasoning": "Long-term buy-and-hold opportunity for rental income",
                "verifications": ["Tenant history", "Tax record review", "Market rental rates"],
                "timeline_days": 21,
                "effort_level": "medium",
                "next_steps": [
                    "Research rental market rates",
                    "Pull tax records and tenant history",
                    "Evaluate financing terms",
                ],
            },
            ExecutionPipeline.PARTNERSHIP: {
                "reasoning": "Partnership/JV opportunity - both parties contribute",
                "verifications": ["Partner vetting", "Legal structure planning"],
                "timeline_days": 14,
                "effort_level": "high",
                "next_steps": [
                    "Clarify contribution structure",
                    "Define profit split",
                    "Get legal template reviewed",
                ],
            },
            ExecutionPipeline.BUSINESS_JV: {
                "reasoning": "Business partnership - requires additional analysis",
                "verifications": ["Business financials", "Legal review", "Partner assessment"],
                "timeline_days": 21,
                "effort_level": "high",
                "next_steps": [
                    "Request last 2 years financials",
                    "Review existing contracts",
                    "Assess partner capabilities",
                ],
            },
            ExecutionPipeline.MANUAL_REVIEW: {
                "reasoning": "Complex or unclear opportunity requires manual expert review",
                "verifications": ["Expert consultation"],
                "timeline_days": 2,
                "effort_level": "high",
                "next_steps": [
                    "Submit to manual underwriting queue",
                    "Provide all available documentation",
                    "Wait for expert assessment",
                ],
            },
        }
        
        return details.get(pipeline, {
            "reasoning": "Unknown pipeline",
            "verifications": [],
            "timeline_days": 14,
            "effort_level": "medium",
        })
    
    def _get_required_verifications(self, classification: str) -> List[str]:
        """Get list of required verifications for classification"""
        
        verifications = {
            "real_estate": [
                "Property exists and matches description",
                "Seller has authority to transact",
                "Title is clear or issues documented",
                "Property value in range",
                "Market conditions support strategy",
            ],
            "business": [
                "Business is legitimate and operating",
                "Financials are accurate and current",
                "No major legal/regulatory issues",
                "Market for product/service is real",
                "Operator capabilities assessed",
            ],
            "jv": [
                "Partner identity verified",
                "Partner financial capacity confirmed",
                "Opportunity is real and available",
                "Deal terms are clear",
                "Legal framework is sound",
            ],
            "arbitrage": [
                "Price difference is real and achievable",
                "Buyer exists at target price",
                "Holding costs are reasonable",
                "Timeline is realistic",
                "No hidden liabilities",
            ],
        }
        
        return verifications.get(classification, ["General opportunity verification"])
