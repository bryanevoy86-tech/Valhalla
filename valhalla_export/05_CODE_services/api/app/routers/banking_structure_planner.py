"""
PACK SC: Banking & Accounts Structure Planner Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.schemas.banking_structure_planner import (
    BankAccountPlanSchema,
    AccountSetupChecklistSchema,
    AccountIncomeMappingSchema,
    AccountStructureSummaryResponse,
)
from app.services.banking_structure_planner import (
    create_account_plan,
    get_account_plan,
    get_all_account_plans,
    get_accounts_by_category,
    update_account_status,
    create_setup_checklist_item,
    get_setup_checklist_for_account,
    create_income_mapping,
    get_account_mappings,
    get_all_active_mappings,
    get_account_structure_summary,
)

router = APIRouter(prefix="/banking", tags=["PACK SC: Banking Structure Planner"])


@router.post("/accounts", response_model=BankAccountPlanSchema)
def create_account(plan: BankAccountPlanSchema, db: Session = Depends(get_db)):
    """Create a new bank account plan."""
    return create_account_plan(db, plan)


@router.get("/accounts", response_model=List[BankAccountPlanSchema])
def list_accounts(db: Session = Depends(get_db)):
    """Get all account plans."""
    return get_all_account_plans(db)


@router.get("/accounts/{account_id}", response_model=BankAccountPlanSchema)
def get_account(account_id: str, db: Session = Depends(get_db)):
    """Get a specific account plan."""
    account = get_account_plan(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account plan not found")
    return account


@router.get("/accounts/category/{category}", response_model=List[BankAccountPlanSchema])
def get_accounts_in_category(category: str, db: Session = Depends(get_db)):
    """Get all accounts in a specific category."""
    return get_accounts_by_category(db, category)


@router.patch("/accounts/{account_id}/status")
def update_status(account_id: str, status: str, db: Session = Depends(get_db)):
    """Update account status (planned, open, verified)."""
    updated = update_account_status(db, account_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Account plan not found")
    return {"status": "updated", "new_status": status}


@router.post("/setup-checklist", response_model=AccountSetupChecklistSchema)
def create_checklist_item(item: AccountSetupChecklistSchema, db: Session = Depends(get_db)):
    """Add a setup step to an account's checklist."""
    return create_setup_checklist_item(db, item)


@router.get("/setup-checklist/{account_plan_id}", response_model=List[AccountSetupChecklistSchema])
def get_checklist(account_plan_id: int, db: Session = Depends(get_db)):
    """Get setup checklist for an account."""
    return get_setup_checklist_for_account(db, account_plan_id)


@router.post("/mappings", response_model=AccountIncomeMappingSchema)
def create_mapping(mapping: AccountIncomeMappingSchema, db: Session = Depends(get_db)):
    """Create an income/expense routing rule."""
    return create_income_mapping(db, mapping)


@router.get("/mappings/{account_id}", response_model=List[AccountIncomeMappingSchema])
def get_mappings(account_id: int, db: Session = Depends(get_db)):
    """Get routing rules for an account."""
    return get_account_mappings(db, account_id)


@router.get("/mappings", response_model=List[AccountIncomeMappingSchema])
def get_active_mappings(db: Session = Depends(get_db)):
    """Get all active routing rules."""
    return get_all_active_mappings(db)


@router.get("/summary", response_model=AccountStructureSummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    """Get overall banking structure summary."""
    return get_account_structure_summary(db)
