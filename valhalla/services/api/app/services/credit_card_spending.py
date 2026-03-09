"""Services for PACK SD: Credit Card & Spending Framework"""

from sqlalchemy.orm import Session
from app.models.credit_card_spending import (
    CreditCardProfile, SpendingRule, SpendingTransaction, MonthlySpendingSummary
)
from app.schemas.credit_card_spending import (
    CreditCardProfileSchema, SpendingRuleSchema, SpendingTransactionSchema, MonthlySummarySchema
)
from datetime import datetime, date
from typing import List, Optional


# ========== CREDIT CARD PROFILE FUNCTIONS ==========

def create_card_profile(db: Session, card_data: CreditCardProfileSchema) -> CreditCardProfile:
    """Create new credit card profile"""
    db_card = CreditCardProfile(**card_data.model_dump())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


def get_card_profile(db: Session, card_id: int) -> Optional[CreditCardProfile]:
    """Get card profile by ID"""
    return db.query(CreditCardProfile).filter(CreditCardProfile.id == card_id).first()


def list_card_profiles(db: Session) -> List[CreditCardProfile]:
    """List all card profiles"""
    return db.query(CreditCardProfile).all()


def update_card_profile(db: Session, card_id: int, card_data: CreditCardProfileSchema) -> CreditCardProfile:
    """Update card profile"""
    db_card = get_card_profile(db, card_id)
    if db_card:
        for key, value in card_data.model_dump(exclude_unset=True).items():
            setattr(db_card, key, value)
        db_card.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_card)
    return db_card


# ========== SPENDING RULE FUNCTIONS ==========

def create_spending_rule(db: Session, rule_data: SpendingRuleSchema) -> SpendingRule:
    """Create spending rule for card"""
    db_rule = SpendingRule(**rule_data.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def get_card_rules(db: Session, card_id: int) -> List[SpendingRule]:
    """Get all rules for a card"""
    return db.query(SpendingRule).filter(SpendingRule.card_id == card_id).all()


def get_rule_for_category(db: Session, card_id: int, category: str) -> Optional[SpendingRule]:
    """Get rule for specific category on card"""
    return db.query(SpendingRule).filter(
        SpendingRule.card_id == card_id,
        SpendingRule.category == category
    ).first()


# ========== TRANSACTION FUNCTIONS ==========

def check_transaction_compliance(
    db: Session, 
    card_id: int, 
    category: str,
    classification: str  # "business" or "personal"
) -> tuple[bool, Optional[str]]:
    """
    Check if transaction matches card rules.
    Returns (is_compliant, flag_reason)
    """
    rule = get_rule_for_category(db, card_id, category)
    
    if not rule:
        return False, f"No rule defined for category '{category}' on this card"
    
    if classification == "business" and not rule.business_allowed:
        return False, f"Business use not allowed for {category}"
    
    if classification == "personal" and not rule.personal_allowed:
        return False, f"Personal use not allowed for {category}"
    
    return True, None


def log_transaction(db: Session, txn_data: SpendingTransactionSchema) -> SpendingTransaction:
    """Log a spending transaction"""
    # Check compliance
    is_compliant, flag_reason = check_transaction_compliance(
        db, txn_data.card_id, txn_data.detected_category or "uncategorized",
        txn_data.user_classification or "unknown"
    )
    
    db_txn = SpendingTransaction(
        **txn_data.model_dump(),
        rule_compliant=is_compliant,
        flagged=not is_compliant,
        flag_reason=flag_reason
    )
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn


def get_flagged_transactions(db: Session, card_id: int, month: Optional[int] = None) -> List[SpendingTransaction]:
    """Get flagged transactions for review"""
    query = db.query(SpendingTransaction).filter(
        SpendingTransaction.card_id == card_id,
        SpendingTransaction.flagged == True
    )
    
    if month:
        query = query.filter(SpendingTransaction.date.op('month')() == month)
    
    return query.all()


# ========== MONTHLY SUMMARY FUNCTIONS ==========

def generate_monthly_summary(db: Session, card_id: int, year: int, month: int) -> MonthlySpendingSummary:
    """Generate monthly spending summary"""
    # Get all transactions for the month
    txns = db.query(SpendingTransaction).filter(
        SpendingTransaction.card_id == card_id,
        SpendingTransaction.date.op('year')() == year,
        SpendingTransaction.date.op('month')() == month
    ).all()
    
    # Calculate totals
    total_business = sum(t.amount for t in txns if t.user_classification == "business")
    total_personal = sum(t.amount for t in txns if t.user_classification == "personal")
    total_flagged = sum(t.amount for t in txns if t.flagged)
    
    # Category breakdown
    category_breakdown = {}
    for txn in txns:
        cat = txn.detected_category or "uncategorized"
        if cat not in category_breakdown:
            category_breakdown[cat] = 0
        category_breakdown[cat] += txn.amount
    
    # Flagged transactions summary
    flagged_txns = [t for t in txns if t.flagged]
    flagged_summary = [
        {
            "date": t.date.isoformat(),
            "merchant": t.merchant,
            "amount": t.amount,
            "reason": t.flag_reason
        }
        for t in flagged_txns
    ]
    
    # Detect recurring transactions (same merchant)
    merchant_counts = {}
    for txn in txns:
        merchant = txn.merchant or "unknown"
        if merchant not in merchant_counts:
            merchant_counts[merchant] = []
        merchant_counts[merchant].append(txn)
    
    subscriptions = [
        {
            "merchant": merchant,
            "count": len(txns_list),
            "total": sum(t.amount for t in txns_list)
        }
        for merchant, txns_list in merchant_counts.items()
        if len(txns_list) > 1  # Assume recurring if multiple transactions
    ]
    
    # Find unusual items (high-value transactions)
    avg_amount = sum(t.amount for t in txns) / len(txns) if txns else 0
    unusual = [
        {
            "date": t.date.isoformat(),
            "merchant": t.merchant,
            "amount": t.amount,
            "category": t.detected_category
        }
        for t in txns
        if t.amount > avg_amount * 3  # Over 3x average
    ]
    
    # Create or update summary
    summary = db.query(MonthlySpendingSummary).filter(
        MonthlySpendingSummary.card_id == card_id,
        MonthlySpendingSummary.year == year,
        MonthlySpendingSummary.month == month
    ).first()
    
    if summary:
        summary.total_business = total_business
        summary.total_personal = total_personal
        summary.total_flagged = total_flagged
        summary.flagged_transactions = flagged_summary
        summary.category_breakdown = category_breakdown
        summary.unusual_items = unusual
        summary.subscription_list = subscriptions
        summary.updated_at = datetime.utcnow()
    else:
        summary = MonthlySpendingSummary(
            card_id=card_id,
            year=year,
            month=month,
            total_business=total_business,
            total_personal=total_personal,
            total_flagged=total_flagged,
            flagged_transactions=flagged_summary,
            category_breakdown=category_breakdown,
            unusual_items=unusual,
            subscription_list=subscriptions
        )
        db.add(summary)
    
    db.commit()
    db.refresh(summary)
    return summary


def get_monthly_summary(db: Session, card_id: int, year: int, month: int) -> Optional[MonthlySpendingSummary]:
    """Get existing monthly summary"""
    return db.query(MonthlySpendingSummary).filter(
        MonthlySpendingSummary.card_id == card_id,
        MonthlySpendingSummary.year == year,
        MonthlySpendingSummary.month == month
    ).first()
