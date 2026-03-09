"""
PACK SI: Real Estate Acquisition & BRRRR Planner
FastAPI router for BRRRR deal tracking and management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.schemas.brrrr_planner import (
    BRRRRDealSchema, BRRRRFundingPlanSchema, BRRRRCashflowEntrySchema,
    BRRRRRefinanceSnapshotSchema, BRRRRSummarySchema, DealLifecycleResponse
)
from app.services import brrrr_planner
from datetime import datetime

router = APIRouter(prefix="/brrrr", tags=["PACK SI: BRRRR Planner"])


@router.post("/deals", response_model=BRRRRDealSchema)
def create_deal(
    deal: BRRRRDealSchema,
    db: Session = Depends(get_db)
):
    """Create a new BRRRR deal in analysis phase."""
    created = brrrr_planner.create_brrrr_deal(
        db,
        deal_id=deal.deal_id,
        address=deal.address,
        purchase_price=deal.purchase_price,
        reno_budget=deal.reno_budget,
        description=deal.description,
        strategy_notes=deal.strategy_notes
    )
    return created


@router.get("/deals", response_model=list[BRRRRDealSchema])
def list_deals(status: str = None, db: Session = Depends(get_db)):
    """List all BRRRR deals, optionally filtered by status."""
    deals = brrrr_planner.list_brrrr_deals(db, status)
    return deals


@router.get("/deals/{deal_id}", response_model=BRRRRDealSchema)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    """Get a BRRRR deal by ID."""
    deal = brrrr_planner.get_brrrr_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.patch("/deals/{deal_id}/status")
def update_status(deal_id: int, new_status: str, db: Session = Depends(get_db)):
    """Update deal status (analysis, in_progress, refinanced, holding)."""
    deal = brrrr_planner.update_deal_status(db, deal_id, new_status)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal.deal_id, "status": deal.status}


@router.patch("/deals/{deal_id}/arv")
def set_arv(deal_id: int, arv: int, db: Session = Depends(get_db)):
    """Set the after-repair value after comp analysis."""
    deal = brrrr_planner.set_deal_arv(db, deal_id, arv)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal.deal_id, "arv": deal.arv}


@router.post("/funding-plans", response_model=BRRRRFundingPlanSchema)
def create_funding(
    plan: BRRRRFundingPlanSchema,
    db: Session = Depends(get_db)
):
    """Create a funding plan for a deal."""
    deal = brrrr_planner.get_brrrr_deal(db, plan.deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    created = brrrr_planner.create_funding_plan(
        db,
        plan_id=plan.plan_id,
        deal_id=plan.deal_id,
        down_payment=plan.down_payment,
        renovation_funds_source=plan.renovation_funds_source,
        holding_costs_plan=plan.holding_costs_plan,
        refinance_strategy=plan.refinance_strategy,
        notes=plan.notes
    )
    return created


@router.get("/funding-plans/{deal_id}", response_model=BRRRRFundingPlanSchema)
def get_funding(deal_id: int, db: Session = Depends(get_db)):
    """Get the funding plan for a deal."""
    plan = brrrr_planner.get_funding_plan(db, deal_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Funding plan not found")
    return plan


@router.post("/cashflow", response_model=BRRRRCashflowEntrySchema)
def log_cashflow(
    entry: BRRRRCashflowEntrySchema,
    db: Session = Depends(get_db)
):
    """Log a monthly cashflow entry (rent and expenses)."""
    deal = brrrr_planner.get_brrrr_deal(db, entry.deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    created = brrrr_planner.log_cashflow_entry(
        db,
        entry_id=entry.entry_id,
        deal_id=entry.deal_id,
        date=entry.date,
        rent=entry.rent,
        expenses=entry.expenses,
        notes=entry.notes
    )
    return created


@router.get("/cashflow/{deal_id}")
def list_cashflow(deal_id: int, db: Session = Depends(get_db)):
    """List all cashflow entries for a deal."""
    deal = brrrr_planner.get_brrrr_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    entries = brrrr_planner.list_cashflow_entries(db, deal_id)
    return entries


@router.get("/cashflow/{deal_id}/average")
def cashflow_average(deal_id: int, db: Session = Depends(get_db)):
    """Get average monthly cashflow metrics."""
    deal = brrrr_planner.get_brrrr_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    avg = brrrr_planner.calculate_monthly_average(db, deal_id)
    return avg


@router.post("/refinance", response_model=BRRRRRefinanceSnapshotSchema)
def log_refinance(
    snapshot: BRRRRRefinanceSnapshotSchema,
    db: Session = Depends(get_db)
):
    """Record a refinance event with new loan terms."""
    deal = brrrr_planner.get_brrrr_deal(db, snapshot.deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    created = brrrr_planner.log_refinance(
        db,
        snapshot_id=snapshot.snapshot_id,
        deal_id=snapshot.deal_id,
        date=snapshot.date,
        new_loan_amount=snapshot.new_loan_amount,
        interest_rate=snapshot.interest_rate,
        cash_out_amount=snapshot.cash_out_amount,
        new_payment=snapshot.new_payment,
        loan_term_months=snapshot.loan_term_months,
        notes=snapshot.notes
    )
    return created


@router.get("/refinance/{deal_id}")
def list_refinances(deal_id: int, db: Session = Depends(get_db)):
    """List all refinance records for a deal."""
    deal = brrrr_planner.get_brrrr_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    snapshots = brrrr_planner.list_refinance_snapshots(db, deal_id)
    return snapshots


@router.post("/summaries", response_model=BRRRRSummarySchema)
def create_summary(
    summary: BRRRRSummarySchema,
    db: Session = Depends(get_db)
):
    """Create a comprehensive deal summary."""
    deal = brrrr_planner.get_brrrr_deal(db, summary.deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    created = brrrr_planner.create_brrrr_summary(
        db,
        summary_id=summary.summary_id,
        deal_id=summary.deal_id,
        purchase_price=summary.purchase_price,
        reno_actual=summary.reno_actual,
        reno_budget=summary.reno_budget,
        arv=summary.arv,
        initial_equity=summary.initial_equity,
        refi_loan_amount=summary.refi_loan_amount,
        cash_out=summary.cash_out,
        current_monthly_cashflow=summary.current_monthly_cashflow,
        annualized_cashflow=summary.annualized_cashflow,
        timeline=summary.timeline
    )
    return created


@router.get("/summaries/{summary_id}", response_model=BRRRRSummarySchema)
def get_summary(summary_id: str, db: Session = Depends(get_db)):
    """Get a BRRRR deal summary."""
    summary = brrrr_planner.get_brrrr_summary(db, summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.get("/metrics/{deal_id}")
def deal_metrics(deal_id: int, db: Session = Depends(get_db)):
    """Get comprehensive metrics and KPIs for a deal."""
    deal = brrrr_planner.get_brrrr_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    metrics = brrrr_planner.calculate_deal_metrics(db, deal_id)
    return metrics
