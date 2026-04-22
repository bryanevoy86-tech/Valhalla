"""
BRRRR analysis service for evaluating deal BRRRR opportunities.
"""

import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from ..models.match import DealBrief

logger = logging.getLogger(__name__)


def analyze_brrrr(db: Session, deal: DealBrief) -> dict:
    """
    Analyze a deal as a BRRRR (Buy, Rehab, Rent, Refinance, Repeat) opportunity.
    
    BRRRR calculations:
    cash_out_estimate = (arv * refinance_ltv) - price - rehab_estimate
    monthly_cashflow_estimate = monthly_rent_estimate - monthly_expense_estimate
    
    Recommendation logic:
    - cash_out >= 0 AND monthly_cashflow >= 200 -> "Proceed"
    - cash_out < 0 BUT monthly_cashflow >= 0 -> "Marginal"
    - monthly_cashflow < 0 -> "Pass"
    - Missing major inputs -> "Incomplete"
    
    Args:
        db: Database session
        deal: DealBrief object with BRRRR data
    
    Returns:
        dict with BRRRR analysis and recommendation
    """
    
    # Get BRRRR inputs, convert to Decimal for safe calculations
    arv = Decimal(deal.arv) if deal.arv else None
    price = Decimal(deal.price) if deal.price else None
    rehab = Decimal(deal.rehab_estimate) if deal.rehab_estimate else None
    monthly_rent = Decimal(deal.monthly_rent_estimate) if deal.monthly_rent_estimate else None
    monthly_expense = Decimal(deal.monthly_expense_estimate) if deal.monthly_expense_estimate else None
    refinance_ltv = Decimal(deal.refinance_ltv) if deal.refinance_ltv else None
    
    # Check for incomplete data
    if not all([arv, price, refinance_ltv, monthly_rent, monthly_expense]):
        logger.warning(f"Deal {deal.id} missing required BRRRR inputs")
        return {
            "deal_id": deal.id,
            "headline": deal.headline,
            "strategy_tag": "brrrr",
            "monthly_rent_estimate": float(monthly_rent) if monthly_rent else None,
            "monthly_expense_estimate": float(monthly_expense) if monthly_expense else None,
            "refinance_ltv": float(refinance_ltv) if refinance_ltv else None,
            "cash_out_estimate": None,
            "monthly_cashflow_estimate": None,
            "recommendation": "Incomplete - Need ARV, Price, Rent, Expenses, and Refinance LTV"
        }
    
    # Calculate cash_out
    # Default rehab to 0 if missing
    rehab_val = rehab if rehab else Decimal(0)
    cash_out = (arv * refinance_ltv) - price - rehab_val
    
    # Calculate monthly cashflow
    monthly_cashflow = monthly_rent - monthly_expense
    
    # Determine recommendation
    if cash_out >= Decimal(0) and monthly_cashflow >= Decimal(200):
        recommendation = "Proceed"
    elif cash_out < Decimal(0) and monthly_cashflow >= Decimal(0):
        recommendation = "Marginal"
    elif monthly_cashflow < Decimal(0):
        recommendation = "Pass"
    else:
        recommendation = "Marginal"  # Between 0-200 cashflow with positive cash_out
    
    # Update deal with calculated values
    deal.cash_out_estimate = cash_out
    deal.monthly_cashflow_estimate = monthly_cashflow
    deal.strategy_tag = "brrrr"
    deal.brrrr_recommendation = recommendation
    db.commit()
    db.refresh(deal)
    
    logger.info(
        f"Deal {deal.id} BRRRR analysis: cash_out=${float(cash_out):,.2f}, "
        f"monthly_cashflow=${float(monthly_cashflow):,.2f}, "
        f"recommendation={recommendation}"
    )
    
    return {
        "deal_id": deal.id,
        "headline": deal.headline,
        "strategy_tag": "brrrr",
        "monthly_rent_estimate": float(monthly_rent),
        "monthly_expense_estimate": float(monthly_expense),
        "refinance_ltv": float(refinance_ltv),
        "cash_out_estimate": float(cash_out),
        "monthly_cashflow_estimate": float(monthly_cashflow),
        "recommendation": recommendation
    }


def update_brrrr_inputs(
    db: Session,
    deal: DealBrief,
    monthly_rent: Optional[float] = None,
    monthly_expense: Optional[float] = None,
    refinance_ltv: Optional[float] = None,
    refinance_rate: Optional[float] = None,
    refinance_term_years: Optional[int] = None
) -> dict:
    """
    Update BRRRR analysis inputs for a deal.
    
    Args:
        db: Database session
        deal: DealBrief object to update
        monthly_rent: Estimated monthly rent (optional)
        monthly_expense: Estimated monthly expenses (optional)
        refinance_ltv: Loan-to-value for refinance (optional)
        refinance_rate: Interest rate for refinance (optional)
        refinance_term_years: Loan term in years (optional)
    
    Returns:
        Updated BRRRR analysis
    """
    
    # Update fields if provided
    if monthly_rent is not None:
        deal.monthly_rent_estimate = Decimal(str(monthly_rent))
    if monthly_expense is not None:
        deal.monthly_expense_estimate = Decimal(str(monthly_expense))
    if refinance_ltv is not None:
        deal.refinance_ltv = Decimal(str(refinance_ltv))
    if refinance_rate is not None:
        deal.refinance_rate = Decimal(str(refinance_rate))
    if refinance_term_years is not None:
        deal.refinance_term_years = refinance_term_years
    
    db.commit()
    db.refresh(deal)
    
    logger.info(
        f"Deal {deal.id} BRRRR inputs updated: "
        f"rent={monthly_rent}, expense={monthly_expense}, ltv={refinance_ltv}"
    )
    
    # Re-analyze with new inputs
    return analyze_brrrr(db, deal)
