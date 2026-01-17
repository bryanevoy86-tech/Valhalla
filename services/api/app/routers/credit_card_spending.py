"""Router for PACK SD: Credit Card & Spending Framework"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.schemas.credit_card_spending import (
    CreditCardProfileSchema, SpendingRuleSchema, SpendingTransactionSchema, SpendingStatusResponse
)
from app.services import credit_card_spending

router = APIRouter(prefix="/cards", tags=["PACK SD: Credit Card & Spending"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== CARD PROFILE ENDPOINTS ==========

@router.post("/profiles", response_model=CreditCardProfileSchema)
def create_card_profile(profile: CreditCardProfileSchema, db: Session = Depends(get_db)):
    """Create new credit card profile"""
    return credit_card_spending.create_card_profile(db, profile)


@router.get("/profiles", response_model=list[CreditCardProfileSchema])
def list_card_profiles(db: Session = Depends(get_db)):
    """List all card profiles"""
    return credit_card_spending.list_card_profiles(db)


@router.get("/profiles/{card_id}", response_model=CreditCardProfileSchema)
def get_card_profile(card_id: int, db: Session = Depends(get_db)):
    """Get card profile details"""
    card = credit_card_spending.get_card_profile(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    return card


# ========== SPENDING RULE ENDPOINTS ==========

@router.post("/rules", response_model=SpendingRuleSchema)
def create_spending_rule(rule: SpendingRuleSchema, db: Session = Depends(get_db)):
    """Create spending rule for card"""
    # Verify card exists
    card = credit_card_spending.get_card_profile(db, rule.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    
    return credit_card_spending.create_spending_rule(db, rule)


@router.get("/rules/{card_id}", response_model=list[SpendingRuleSchema])
def get_card_rules(card_id: int, db: Session = Depends(get_db)):
    """Get all rules for a card"""
    card = credit_card_spending.get_card_profile(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    
    return credit_card_spending.get_card_rules(db, card_id)


# ========== TRANSACTION ENDPOINTS ==========

@router.post("/transactions", response_model=SpendingTransactionSchema)
def log_transaction(txn: SpendingTransactionSchema, db: Session = Depends(get_db)):
    """Log spending transaction with compliance check"""
    card = credit_card_spending.get_card_profile(db, txn.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    
    return credit_card_spending.log_transaction(db, txn)


@router.get("/flagged/{card_id}", response_model=list[SpendingTransactionSchema])
def get_flagged_transactions(card_id: int, month: int = None, db: Session = Depends(get_db)):
    """Get flagged transactions for review"""
    card = credit_card_spending.get_card_profile(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    
    return credit_card_spending.get_flagged_transactions(db, card_id, month)


# ========== MONTHLY SUMMARY ENDPOINTS ==========

@router.post("/summary/{card_id}/{year}/{month}", response_model=SpendingStatusResponse)
def generate_monthly_summary(card_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """Generate monthly spending summary"""
    card = credit_card_spending.get_card_profile(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    
    summary = credit_card_spending.generate_monthly_summary(db, card_id, year, month)
    
    return SpendingStatusResponse(
        card_id=card_id,
        month=f"{year}-{month:02d}",
        total_transactions=summary.category_breakdown.__len__() if summary.category_breakdown else 0,
        compliant_count=len(summary.flagged_transactions) if summary.flagged_transactions else 0,
        flagged_count=len(summary.flagged_transactions) if summary.flagged_transactions else 0,
        compliance_percentage=100 - (summary.total_flagged / (summary.total_business + summary.total_personal) * 100) if (summary.total_business + summary.total_personal) > 0 else 100,
        flagged_amount_cents=summary.total_flagged,
        categories=summary.category_breakdown or {},
        requires_review=summary.total_flagged > 0
    )


@router.get("/summary/{card_id}/{year}/{month}", response_model=SpendingStatusResponse)
def get_monthly_summary(card_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """Get monthly spending summary"""
    card = credit_card_spending.get_card_profile(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card profile not found")
    
    summary = credit_card_spending.get_monthly_summary(db, card_id, year, month)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    
    return SpendingStatusResponse(
        card_id=card_id,
        month=f"{year}-{month:02d}",
        total_transactions=len(summary.category_breakdown) if summary.category_breakdown else 0,
        compliant_count=0,  # Would require transaction list
        flagged_count=len(summary.flagged_transactions) if summary.flagged_transactions else 0,
        compliance_percentage=100 - (summary.total_flagged / (summary.total_business + summary.total_personal) * 100) if (summary.total_business + summary.total_personal) > 0 else 100,
        flagged_amount_cents=summary.total_flagged,
        categories=summary.category_breakdown or {},
        requires_review=summary.total_flagged > 0
    )
