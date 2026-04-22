"""
Buyer matching models for deal-to-buyer intelligence.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, func
from ..core.db import Base

class Buyer(Base):
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    email = Column(String(160), nullable=True)
    phone = Column(String(40), nullable=True)
    regions = Column(String(240), nullable=True)        # comma list e.g., "Winnipeg,Brandon,CA-MB"
    property_types = Column(String(160), nullable=True) # "SFH,Duplex,Triplex"
    min_price = Column(Numeric(18,2), nullable=True)
    max_price = Column(Numeric(18,2), nullable=True)
    min_beds = Column(Integer, nullable=True)
    min_baths = Column(Integer, nullable=True)
    tags = Column(String(240), nullable=True)           # freeform labels
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DealBrief(Base):
    __tablename__ = "deal_briefs"
    id = Column(Integer, primary_key=True)
    headline = Column(String(240), nullable=False)      # e.g., "SFH in Transcona, solid bones"
    region = Column(String(120), nullable=True)         # city/area or code
    property_type = Column(String(40), nullable=True)   # "SFH","Duplex",...
    price = Column(Numeric(18,2), nullable=True)
    beds = Column(Integer, nullable=True)
    baths = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="active")  # active, under_contract, sold, archived
    disposition_status = Column(String(40), nullable=True)  # new, buyer_review, offer_out, assigned, closed, dead
    disposition_notes = Column(Text, nullable=True)
    
    # Flip analysis fields
    arv = Column(Numeric(18,2), nullable=True)  # After Repair Value
    rehab_estimate = Column(Numeric(18,2), nullable=True)  # Estimated rehab cost
    holding_cost_estimate = Column(Numeric(18,2), nullable=True)  # Carrying costs during flip
    selling_cost_estimate = Column(Numeric(18,2), nullable=True)  # Realtor commissions, closing costs
    projected_profit = Column(Numeric(18,2), nullable=True)  # Calculated: arv - price - rehab - holding - selling
    strategy_tag = Column(String(40), nullable=True)  # e.g., "flip", "brrrr", "wholesale"
    
    # BRRRR analysis fields (Buy, Rehab, Rent, Refinance, Repeat)
    monthly_rent_estimate = Column(Numeric(10,2), nullable=True)  # Estimated monthly rent
    monthly_expense_estimate = Column(Numeric(10,2), nullable=True)  # Estimated monthly expenses (taxes, insurance, maintenance)
    refinance_ltv = Column(Numeric(5,4), nullable=True)  # Loan-to-value for refinance (0.75 = 75%)
    refinance_rate = Column(Numeric(6,4), nullable=True)  # Interest rate for refinance
    refinance_term_years = Column(Integer, nullable=True)  # Loan term for refinance
    cash_out_estimate = Column(Numeric(18,2), nullable=True)  # Calculated: (arv * refinance_ltv) - price - rehab
    monthly_cashflow_estimate = Column(Numeric(10,2), nullable=True)  # Calculated: monthly_rent - monthly_expense
    brrrr_recommendation = Column(String(40), nullable=True)  # Proceed, Marginal, Pass, Incomplete
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
