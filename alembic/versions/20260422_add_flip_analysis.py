"""Add flip analysis fields to deal_briefs

Revision ID: 20260422_add_flip_analysis
Revises: 20260422_add_buyer_matching
Create Date: 2026-04-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260422_add_flip_analysis'
down_revision = '20260422_add_buyer_matching'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add flip analysis columns to deal_briefs."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Get existing columns
    existing_columns = [c['name'] for c in inspector.get_columns('deal_briefs')]
    
    # Add flip analysis fields if they don't exist
    if "arv" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("arv", sa.Numeric(18, 2), nullable=True))
    
    if "rehab_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("rehab_estimate", sa.Numeric(18, 2), nullable=True))
    
    if "holding_cost_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("holding_cost_estimate", sa.Numeric(18, 2), nullable=True))
    
    if "selling_cost_estimate" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("selling_cost_estimate", sa.Numeric(18, 2), nullable=True))
    
    if "projected_profit" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("projected_profit", sa.Numeric(18, 2), nullable=True))
    
    if "strategy_tag" not in existing_columns:
        op.add_column("deal_briefs", sa.Column("strategy_tag", sa.String(40), nullable=True))


def downgrade() -> None:
    """Remove flip analysis columns from deal_briefs."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Get existing columns
    existing_columns = [c['name'] for c in inspector.get_columns('deal_briefs')]
    
    # Drop flip columns if they exist
    flip_columns = ["arv", "rehab_estimate", "holding_cost_estimate", "selling_cost_estimate", "projected_profit", "strategy_tag"]
    for col in flip_columns:
        if col in existing_columns:
            op.drop_column("deal_briefs", col)
