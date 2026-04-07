"""
PACK SI: Real Estate Acquisition & BRRRR Planner
Service functions for BRRRR deal tracking, funding, cashflow, and refinancing
"""
from sqlalchemy.orm import Session
from app.models.brrrr_planner import (
    BRRRRDeal, BRRRRFundingPlan, BRRRRCashflowEntry, BRRRRRefinanceSnapshot, BRRRRSummary
)
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


def create_brrrr_deal(
    db: Session,
    deal_id: str,
    address: str,
    purchase_price: int,
    reno_budget: int,
    description: Optional[str] = None,
    strategy_notes: Optional[str] = None
) -> BRRRRDeal:
    """Create a new BRRRR deal in analysis phase."""
    deal = BRRRRDeal(
        deal_id=deal_id,
        address=address,
        description=description,
        purchase_price=purchase_price,
        reno_budget=reno_budget,
        strategy_notes=strategy_notes,
        status="analysis"
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def get_brrrr_deal(db: Session, deal_id: int) -> Optional[BRRRRDeal]:
    """Get a BRRRR deal by ID."""
    return db.query(BRRRRDeal).filter(BRRRRDeal.id == deal_id).first()


def list_brrrr_deals(db: Session, status: Optional[str] = None) -> List[BRRRRDeal]:
    """List all BRRRR deals, optionally filtered by status."""
    query = db.query(BRRRRDeal)
    if status:
        query = query.filter(BRRRRDeal.status == status)
    return query.all()


def update_deal_status(db: Session, deal_id: int, new_status: str) -> BRRRRDeal:
    """Update deal status (analysis, in_progress, refinanced, holding)."""
    deal = get_brrrr_deal(db, deal_id)
    if deal:
        deal.status = new_status
        deal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deal)
    return deal


def set_deal_arv(db: Session, deal_id: int, arv: int) -> BRRRRDeal:
    """Set the after-repair value (user provides this after comp analysis)."""
    deal = get_brrrr_deal(db, deal_id)
    if deal:
        deal.arv = arv
        deal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deal)
    return deal


def create_funding_plan(
    db: Session,
    plan_id: str,
    deal_id: int,
    down_payment: int,
    renovation_funds_source: Optional[str] = None,
    holding_costs_plan: Optional[str] = None,
    refinance_strategy: Optional[str] = None,
    notes: Optional[str] = None
) -> BRRRRFundingPlan:
    """Create a funding plan for a deal."""
    plan = BRRRRFundingPlan(
        plan_id=plan_id,
        deal_id=deal_id,
        down_payment=down_payment,
        renovation_funds_source=renovation_funds_source,
        holding_costs_plan=holding_costs_plan,
        refinance_strategy=refinance_strategy,
        notes=notes
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_funding_plan(db: Session, deal_id: int) -> Optional[BRRRRFundingPlan]:
    """Get the funding plan for a deal."""
    return db.query(BRRRRFundingPlan).filter(BRRRRFundingPlan.deal_id == deal_id).first()


def log_cashflow_entry(
    db: Session,
    entry_id: str,
    deal_id: int,
    date: datetime,
    rent: int,
    expenses: int,
    notes: Optional[str] = None
) -> BRRRRCashflowEntry:
    """Log a monthly cashflow entry (rent in, expenses out)."""
    net = rent - expenses
    
    entry = BRRRRCashflowEntry(
        entry_id=entry_id,
        deal_id=deal_id,
        date=date,
        rent=rent,
        expenses=expenses,
        net=net,
        notes=notes
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_cashflow_entry(db: Session, entry_id: str) -> Optional[BRRRRCashflowEntry]:
    """Get a cashflow entry by ID."""
    return db.query(BRRRRCashflowEntry).filter(BRRRRCashflowEntry.entry_id == entry_id).first()


def list_cashflow_entries(db: Session, deal_id: int) -> List[BRRRRCashflowEntry]:
    """List all cashflow entries for a deal."""
    return db.query(BRRRRCashflowEntry).filter(BRRRRCashflowEntry.deal_id == deal_id).order_by(
        BRRRRCashflowEntry.date
    ).all()


def calculate_monthly_average(db: Session, deal_id: int) -> Dict[str, int]:
    """Calculate average monthly rent, expenses, and net cashflow."""
    entries = list_cashflow_entries(db, deal_id)
    if not entries:
        return {"avg_rent": 0, "avg_expenses": 0, "avg_net": 0}

    avg_rent = int(sum(e.rent for e in entries) / len(entries))
    avg_expenses = int(sum(e.expenses for e in entries) / len(entries))
    avg_net = int(sum(e.net for e in entries) / len(entries))

    return {"avg_rent": avg_rent, "avg_expenses": avg_expenses, "avg_net": avg_net}


def log_refinance(
    db: Session,
    snapshot_id: str,
    deal_id: int,
    date: datetime,
    new_loan_amount: int,
    interest_rate: float,
    cash_out_amount: int,
    new_payment: int,
    loan_term_months: Optional[int] = None,
    notes: Optional[str] = None
) -> BRRRRRefinanceSnapshot:
    """Record a refinance event with new loan terms and cash out."""
    snapshot = BRRRRRefinanceSnapshot(
        snapshot_id=snapshot_id,
        deal_id=deal_id,
        date=date,
        new_loan_amount=new_loan_amount,
        interest_rate=interest_rate,
        loan_term_months=loan_term_months or 360,  # default to 30-year
        cash_out_amount=cash_out_amount,
        new_payment=new_payment,
        notes=notes
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_refinance_snapshot(db: Session, snapshot_id: str) -> Optional[BRRRRRefinanceSnapshot]:
    """Get a refinance snapshot by ID."""
    return db.query(BRRRRRefinanceSnapshot).filter(
        BRRRRRefinanceSnapshot.snapshot_id == snapshot_id
    ).first()


def list_refinance_snapshots(db: Session, deal_id: int) -> List[BRRRRRefinanceSnapshot]:
    """List all refinance records for a deal."""
    return db.query(BRRRRRefinanceSnapshot).filter(
        BRRRRRefinanceSnapshot.deal_id == deal_id
    ).order_by(BRRRRRefinanceSnapshot.date).all()


def create_brrrr_summary(
    db: Session,
    summary_id: str,
    deal_id: int,
    purchase_price: int,
    reno_actual: Optional[int] = None,
    reno_budget: Optional[int] = None,
    arv: Optional[int] = None,
    initial_equity: Optional[int] = None,
    refi_loan_amount: Optional[int] = None,
    cash_out: Optional[int] = None,
    current_monthly_cashflow: Optional[int] = None,
    annualized_cashflow: Optional[int] = None,
    timeline: Optional[Dict[str, Any]] = None
) -> BRRRRSummary:
    """Create a comprehensive deal summary."""
    summary = BRRRRSummary(
        summary_id=summary_id,
        deal_id=deal_id,
        purchase_price=purchase_price,
        reno_actual=reno_actual,
        reno_budget=reno_budget,
        arv=arv,
        initial_equity=initial_equity,
        refi_loan_amount=refi_loan_amount,
        cash_out=cash_out,
        current_monthly_cashflow=current_monthly_cashflow,
        annualized_cashflow=annualized_cashflow,
        timeline=timeline
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def get_brrrr_summary(db: Session, summary_id: str) -> Optional[BRRRRSummary]:
    """Get a BRRRR deal summary by ID."""
    return db.query(BRRRRSummary).filter(BRRRRSummary.summary_id == summary_id).first()


def calculate_deal_metrics(db: Session, deal_id: int) -> Dict[str, Any]:
    """
    Aggregate deal metrics: timeline, cashflow history, refinance impact.
    """
    deal = get_brrrr_deal(db, deal_id)
    if not deal:
        return {}

    cashflow_entries = list_cashflow_entries(db, deal_id)
    refi = list_refinance_snapshots(db, deal_id)

    months_held = 0
    if deal.acquisition_date and (deal.reno_end_date or cashflow_entries):
        months_held = (datetime.utcnow() - deal.acquisition_date).days // 30

    return {
        "deal_id": deal.deal_id,
        "address": deal.address,
        "purchase_price": deal.purchase_price,
        "arv": deal.arv,
        "months_held": months_held,
        "cashflow_months": len(cashflow_entries),
        "refinanced": len(refi) > 0,
        "refi_count": len(refi),
        "status": deal.status
    }
