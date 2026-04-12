"""
Execution Assessment Service - applies conservative buffers and calculates value/cost/profit
"""
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ExecutionAssessmentService:
    """
    Applies conservative buffers to real estate assessments.
    
    V1 Conservative Rules:
    - ARV (After Repair Value): -15% buffer on estimates
    - Repair costs: +30% buffer on estimates  
    - Operating costs: +20% buffer on estimates
    - Confidence floor: <50% triggers safe mode
    - Risk ceiling: >70% blocks execution
    """
    
    # Default buffers (as multipliers)
    DEFAULT_ARV_BUFFER = 0.85  # 15% reduction
    DEFAULT_REPAIR_BUFFER = 1.30  # 30% increase
    DEFAULT_OPERATING_BUFFER = 1.20  # 20% increase
    DEFAULT_CONFIDENCE_FLOOR = 50
    DEFAULT_RISK_CEILING = 70
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.buffers = {
            "arv": self.DEFAULT_ARV_BUFFER,
            "repair": self.DEFAULT_REPAIR_BUFFER,
            "operating": self.DEFAULT_OPERATING_BUFFER,
        }
    
    def assess_real_estate_deal(
        self,
        raw_estimate: dict,
        confidence: float = 50,
    ) -> dict:
        """
        Apply conservative buffers to real estate opportunity.
        
        Args:
            raw_estimate: {
                "arv_estimate": float,  # After-repair value estimate
                "repair_estimate": float,  # Estimated repairs needed
                "purchase_price": float,  # Asking/offer price
                "operating_cost": float,  # Monthly operating cost
            }
            confidence: Confidence level 0-100
        
        Returns: {
            "estimated_value": float,  # Conservative ARV
            "estimated_repair_cost": float,  # Conservative repair budget
            "estimated_purchase_cost": float,  # Conservative purchase cost
            "estimated_operating_cost": float,  # Conservative operating cost
            "estimated_profit": float,  # value - (purchase + repairs + operating)
            "confidence_score": float,  # 0-100
            "risk_score": float,  # 0-100
            "confidence_level": str,  # low/medium/high
            "safe_mode": bool,  # True if confidence < floor OR risk > ceiling
            "blocked": bool,  # True if fundamentally broken
            "reason": str,  # Why blocked/safe mode
        }
        """
        
        # Validate inputs
        errors = []
        if not isinstance(raw_estimate, dict):
            errors.append("raw_estimate must be dict")
        
        arv_estimate = raw_estimate.get("arv_estimate", 0)
        repair_estimate = raw_estimate.get("repair_estimate", 0)
        purchase_price = raw_estimate.get("purchase_price", 0)
        operating_cost = raw_estimate.get("operating_cost", 0)
        
        if arv_estimate <= 0:
            errors.append("arv_estimate must be > 0")
        if purchase_price < 0:
            errors.append("purchase_price cannot be negative")
        if repair_estimate < 0:
            errors.append("repair_estimate cannot be negative")
        
        if errors:
            return {
                "estimated_value": 0,
                "estimated_repair_cost": 0,
                "estimated_purchase_cost": purchase_price,
                "estimated_operating_cost": 0,
                "estimated_profit": 0,
                "confidence_score": 0,
                "risk_score": 100,
                "confidence_level": "low",
                "safe_mode": True,
                "blocked": True,
                "reason": f"Assessment failed validation: {', '.join(errors)}"
            }
        
        # Apply conservative buffers
        conservative_arv = arv_estimate * self.buffers["arv"]
        conservative_repair = repair_estimate * self.buffers["repair"]
        conservative_operating = operating_cost * self.buffers["operating"]
        
        # Calculate profit (simplified)
        total_cost = purchase_price + conservative_repair + conservative_operating
        estimated_profit = conservative_arv - total_cost
        
        # Calculate profit margin %
        margin_pct = (estimated_profit / conservative_arv * 100) if conservative_arv > 0 else 0
        
        # Risk calculation based on deal metrics
        risk_score = self._calculate_risk_score(
            arv=conservative_arv,
            purchase=purchase_price,
            repairs=conservative_repair,
            margin=margin_pct
        )
        
        # Confidence normalization
        normalized_confidence = max(0, min(100, confidence))
        confidence_level = self._confidence_to_level(normalized_confidence)
        
        # Trigger safe mode if confidence low or risk high
        safe_mode = (
            normalized_confidence < self.DEFAULT_CONFIDENCE_FLOOR or
            risk_score > self.DEFAULT_RISK_CEILING
        )
        
        # Block if fundamentally broken
        blocked = (
            estimated_profit <= 0 or
            margin_pct < 5  # Less than 5% margin
        )
        
        blocker_reason = None
        if blocked and estimated_profit <= 0:
            blocker_reason = "Negative or zero profit - deal doesn't make sense"
        elif blocked:
            blocker_reason = f"Profit margin only {margin_pct:.1f}% - below 5% threshold"
        
        return {
            "estimated_value": round(conservative_arv, 2),
            "estimated_repair_cost": round(conservative_repair, 2),
            "estimated_purchase_cost": round(purchase_price, 2),
            "estimated_operating_cost": round(conservative_operating, 2),
            "estimated_profit": round(estimated_profit, 2),
            "confidence_score": round(normalized_confidence, 1),
            "risk_score": round(risk_score, 1),
            "confidence_level": confidence_level,
            "safe_mode": safe_mode,
            "blocked": blocked,
            "reason": blocker_reason or ("Safe mode: Low confidence" if safe_mode else "")
        }
    
    def _calculate_risk_score(self, arv: float, purchase: float, repairs: float, margin: float) -> float:
        """
        Calculate risk score 0-100.
        Higher = riskier.
        
        Factors:
        - LTC (Loan to Cost): > 80% is risky
        - Repair to Value: > 30% is risky
        - Profit margin: < 10% is risky
        """
        
        total_cost = purchase + repairs
        
        # LTC factor (higher cost ratio = higher risk)
        ltc = (total_cost / arv * 100) if arv > 0 else 100
        ltc_risk = min(100, max(0, (ltc - 60) * 2))  # 60% = 0 risk, 80% = 40 risk
        
        # Repair to value factor
        repair_ratio = (repairs / arv * 100) if arv > 0 else 0
        repair_risk = min(50, max(0, (repair_ratio - 15) * 1.5))
        
        # Margin factor
        margin_risk = max(0, (25 - margin) * 2)  # 25% margin = 0 risk, 0% = 50 risk
        
        # Combine (weighted average)
        risk = (ltc_risk * 0.4) + (repair_risk * 0.35) + (margin_risk * 0.25)
        
        return min(100, max(0, risk))
    
    def _confidence_to_level(self, score: float) -> str:
        """Convert confidence score to label"""
        if score >= 75:
            return "high"
        elif score >= 50:
            return "medium"
        else:
            return "low"
    
    def assess_business_opportunity(self, raw_estimate: dict, confidence: float = 40) -> dict:
        """
        Assess non-real-estate business opportunity.
        More conservative baseline (lower confidence by default).
        """
        
        # For V1, business opportunities get lower default confidence
        # and are flagged for manual review
        
        result = self.assess_real_estate_deal(raw_estimate, confidence=confidence)
        result["safe_mode"] = True  # Always safe mode for business deals in V1
        result["reason"] = "Business opportunity - manual underwriter review required"
        
        return result
    
    def get_alternative_strategies(self, deal_type: str, profit: float, margin: float) -> list:
        """Get alternative strategies based on deal type and profitability"""
        
        strategies = {
            "real_estate": {
                "high_profit": ["wholesale", "buy_and_hold", "fnh", "auction"],
                "medium_profit": ["wholesale", "fnh"],
                "low_profit": ["wholesale (low profit)"],
            },
            "business": ["partnership", "operator_fee", "equity_stake"],
        }
        
        if deal_type == "real_estate":
            if profit > 30000:
                return strategies["real_estate"]["high_profit"]
            elif profit > 10000:
                return strategies["real_estate"]["medium_profit"]
            else:
                return strategies["real_estate"]["low_profit"]
        else:
            return strategies.get(deal_type, [])


class RiskAnalyzer:
    """Separate analyzer for risk scoring"""
    
    RISK_FACTORS = {
        "liquidity_risk": 15,  # Can we sell it quickly?
        "concentration_risk": 10,  # Are we over-exposed?
        "execution_risk": 25,  # Can we actually do the work?
        "market_risk": 20,  # Will market hold?
        "regulatory_risk": 10,  # Any compliance issues?
        "structural_risk": 20,  # Physical soundness?
    }
    
    @staticmethod
    def calculate_composite_risk(factors: dict) -> float:
        """
        Calculate composite risk from individual factors.
        
        Args:
            factors: {"liquidity": 20, "execution": 35, ...}
        
        Returns: 0-100 risk score
        """
        if not factors:
            return 50  # Default neutral
        
        total = sum(factors.values())
        count = len(factors)
        
        return min(100, max(0, total / count))
