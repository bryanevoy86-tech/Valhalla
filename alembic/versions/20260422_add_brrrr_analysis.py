"""Add BRRRR analysis fields to deal_briefs

Revision ID: 20260422_add_brrrr_analysis
Revises: 20260422_add_flip_analysis
Create Date: 2026-04-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260422_add_brrrr_analysis'
down_revision = '20260422_add_flip_analysis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add BRRRR analysis columns to deal_briefs."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Get existing columns
    existing_columns = [c['name'] for c in inspector.get_columns('deal_briefs')]
    
    # Add BRRRR analysis fields if they don't exist
    if "monthly_rent_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("monthly_rent_estimate", sa.Numeric(10, 2), nullable=True))
    
    if "monthly_expense_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("monthly_expense_estimate", sa.Numeric(10, 2), nullable=True))
    
    if "refinance_ltv" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("refinance_ltv", sa.Numeric(5, 4), nullable=True))
    
    if "refinance_rate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("refinance_rate", sa.Numeric(6, 4), nullable=True))
    
    if "refinance_term_years" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("refinance_term_years", sa.Integer, nullable=True))
    
    if "cash_out_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("cash_out_estimate", sa.Numeric(18, 2), nullable=True))
    
    if "monthly_cashflow_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("monthly_cashflow_estimate", sa.Numeric(10, 2), nullable=True))
    
    if "brrrr_recommendation" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("brrrr_recommendation", sa.String(40), nullable=True))


def downgrade() -> None:
    """Remove BRRRR analysis columns from deal_briefs."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Get existing columns
    existing_columns = [c['name'] for c in inspector.get_columns('deal_briefs')]
    
    # Drop BRRRR columns if they exist
    brrrr_columns = [
        "monthly_rent_estimate",
        "monthly_expense_estimate",
        "refinance_ltv",
        "refinance_rate",
        "refinance_term_years",
        "cash_out_estimate",
        "monthly_cashflow_estimate",
        "brrrr_recommendation"
    ]
    for col in brrrr_columns:
        if col in existing_columns:
            op.drop_column("deal_briefs", col)
