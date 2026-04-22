"""
Flip analysis service for evaluating deal flip opportunities.
"""

import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from ..models.match import DealBrief

logger = logging.getLogger(__name__)


def analyze_flip(db: Session, deal: DealBrief) -> dict:
    """
    Analyze a deal as a flip opportunity and compute projected profit.
    
    Flip profit formula:
    projected_profit = arv - price - rehab_estimate - holding_cost_estimate - selling_cost_estimate
    
    Recommendation logic:
    - projected_profit >= 30000 -> Proceed
    - projected_profit 10000 to 29999 -> Marginal
    - projected_profit < 10000 -> Pass
    
    Args:
        db: Database session
        deal: DealBrief object with flip data
    
    Returns:
        dict with flip analysis and recommendation
    """
    
    # Get flip inputs, convert to Decimal for safe calculations
    arv = Decimal(deal.arv) if deal.arv else None
    price = Decimal(deal.price) if deal.price else None
    rehab = Decimal(deal.rehab_estimate) if deal.rehab_estimate else None
    holding = Decimal(deal.holding_cost_estimate) if deal.holding_cost_estimate else None
    selling = Decimal(deal.selling_cost_estimate) if deal.selling_cost_estimate else None
    
    # Validate minimum inputs
    if not arv or not price:
        logger.warning(f"Deal {deal.id} missing required flip inputs (arv or price)")
        return {
            "deal_id": deal.id,
            "headline": deal.headline,
            "strategy_tag": "flip",
            "arv": float(arv) if arv else None,
            "rehab_estimate": float(rehab) if rehab else None,
            "holding_cost_estimate": float(holding) if holding else None,
            "selling_cost_estimate": float(selling) if selling else None,
            "projected_profit": None,
            "recommendation": "Incomplete - Need ARV and Purchase Price"
        }
    
    # Calculate projected profit
    # Default to 0 for missing estimates
    rehab_val = rehab if rehab else Decimal(0)
    holding_val = holding if holding else Decimal(0)
    selling_val = selling if selling else Decimal(0)
    
    projected_profit = arv - price - rehab_val - holding_val - selling_val
    
    # Determine recommendation
    if projected_profit >= Decimal(30000):
        recommendation = "Proceed"
    elif projected_profit >= Decimal(10000):
        recommendation = "Marginal"
    else:
        recommendation = "Pass"
    
    # Update deal with calculated values
    deal.projected_profit = projected_profit
    deal.strategy_tag = "flip"
    db.commit()
    db.refresh(deal)
    
    logger.info(
        f"Deal {deal.id} flip analysis: profit=${float(projected_profit):,.2f}, "
        f"recommendation={recommendation}"
    )
    
    return {
        "deal_id": deal.id,
        "headline": deal.headline,
        "strategy_tag": "flip",
        "arv": float(arv),
        "price": float(price),
        "rehab_estimate": float(rehab_val),
        "holding_cost_estimate": float(holding_val),
        "selling_cost_estimate": float(selling_val),
        "projected_profit": float(projected_profit),
        "recommendation": recommendation
    }


def update_flip_inputs(
    db: Session,
    deal: DealBrief,
    arv: Optional[float] = None,
    rehab: Optional[float] = None,
    holding: Optional[float] = None,
    selling: Optional[float] = None
) -> dict:
    """
    Update flip analysis inputs for a deal.
    
    Args:
        db: Database session
        deal: DealBrief object to update
        arv: After Repair Value (optional)
        rehab: Rehab estimate (optional)
        holding: Holding cost estimate (optional)
        selling: Selling cost estimate (optional)
    
    Returns:
        Updated flip analysis
    """
    
    # Update fields if provided
    if arv is not None:
        deal.arv = Decimal(str(arv))
    if rehab is not None:
        deal.rehab_estimate = Decimal(str(rehab))
    if holding is not None:
        deal.holding_cost_estimate = Decimal(str(holding))
    if selling is not None:
        deal.selling_cost_estimate = Decimal(str(selling))
    
    db.commit()
    db.refresh(deal)
    
    logger.info(
        f"Deal {deal.id} flip inputs updated: "
        f"arv={arv}, rehab={rehab}, holding={holding}, selling={selling}"
    )
    
    # Re-analyze with new inputs
    return analyze_flip(db, deal)
