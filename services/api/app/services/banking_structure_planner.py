"""
PACK SC: Banking & Accounts Structure Planner Services
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.models.banking_structure_planner import (
    BankAccountPlan,
    AccountSetupChecklist,
    AccountIncomeMapping,
)
from app.schemas.banking_structure_planner import (
    BankAccountPlanSchema,
    AccountSetupChecklistSchema,
    AccountIncomeMappingSchema,
    AccountStructureSummaryResponse,
)


def create_account_plan(db: Session, plan: BankAccountPlanSchema) -> BankAccountPlan:
    """Create a new bank account plan."""
    db_plan = BankAccountPlan(
        account_id=plan.account_id,
        name=plan.name,
        category=plan.category,
        purpose=plan.purpose,
        institution=plan.institution,
        status=plan.status,
        notes=plan.notes,
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


def get_account_plan(db: Session, account_id: str) -> Optional[BankAccountPlan]:
    """Get an account plan by account_id."""
    return db.query(BankAccountPlan).filter(BankAccountPlan.account_id == account_id).first()


def get_all_account_plans(db: Session) -> List[BankAccountPlan]:
    """Get all account plans."""
    return db.query(BankAccountPlan).all()


def get_accounts_by_category(db: Session, category: str) -> List[BankAccountPlan]:
    """Get all accounts in a specific category."""
    return db.query(BankAccountPlan).filter(BankAccountPlan.category == category).all()


def update_account_status(
    db: Session, account_id: str, new_status: str
) -> Optional[BankAccountPlan]:
    """Update account status (planned, open, verified)."""
    plan = get_account_plan(db, account_id)
    if not plan:
        return None
    
    plan.status = new_status
    db.commit()
    db.refresh(plan)
    return plan


def create_setup_checklist_item(
    db: Session, item: AccountSetupChecklistSchema
) -> AccountSetupChecklist:
    """Create a setup checklist item for an account."""
    db_item = AccountSetupChecklist(
        account_plan_id=item.account_plan_id,
        step_name=item.step_name,
        is_completed=item.is_completed,
        documents_required=item.documents_required,
        uploaded_filename=item.uploaded_filename,
        notes=item.notes,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_setup_checklist_for_account(
    db: Session, account_plan_id: int
) -> List[AccountSetupChecklist]:
    """Get all setup steps for an account."""
    return db.query(AccountSetupChecklist).filter(
        AccountSetupChecklist.account_plan_id == account_plan_id
    ).all()


def create_income_mapping(db: Session, mapping: AccountIncomeMappingSchema) -> AccountIncomeMapping:
    """Create an income/expense routing rule."""
    db_mapping = AccountIncomeMapping(
        target_account_id=mapping.target_account_id,
        source_type=mapping.source_type,
        source_name=mapping.source_name,
        percentage=mapping.percentage,
        fixed_amount=mapping.fixed_amount,
        is_active=mapping.is_active,
        notes=mapping.notes,
    )
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


def get_account_mappings(db: Session, account_id: int) -> List[AccountIncomeMapping]:
    """Get all routing rules for an account."""
    return db.query(AccountIncomeMapping).filter(
        AccountIncomeMapping.target_account_id == account_id
    ).all()


def get_all_active_mappings(db: Session) -> List[AccountIncomeMapping]:
    """Get all active routing rules."""
    return db.query(AccountIncomeMapping).filter(AccountIncomeMapping.is_active).all()


def get_account_structure_summary(db: Session) -> AccountStructureSummaryResponse:
    """Generate summary of account structure."""
    all_accounts = get_all_account_plans(db)
    all_mappings = db.query(AccountIncomeMapping).all()
    active_mappings = db.query(AccountIncomeMapping).filter(
        AccountIncomeMapping.is_active
    ).all()
    verified_accounts = [a for a in all_accounts if a.status == "verified"]
    
    # Count by category
    categories_count: Dict[str, int] = {}
    for account in all_accounts:
        categories_count[account.category] = categories_count.get(account.category, 0) + 1
    
    return AccountStructureSummaryResponse(
        total_accounts=len(all_accounts),
        accounts_by_category=categories_count,
        total_mappings=len(all_mappings),
        active_mappings=len(active_mappings),
        accounts_ready_for_use=len(verified_accounts),
    )
