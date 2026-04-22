"""add_deal_disposition

Revision ID: 20260422_001
Revises: f2af0b1c2d4b
Create Date: 2026-04-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260422_001"
down_revision: Union[str, Sequence[str], None] = "f2af0b1c2d4b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add disposition_status and disposition_notes columns to deal_briefs table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if deal_briefs table exists and columns don't already exist
    if "deal_briefs" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("deal_briefs")]
        
        # Add disposition_status if it doesn't exist
        if "disposition_status" not in columns:
            op.add_column(
                "deal_briefs",
                sa.Column("disposition_status", sa.String(40), nullable=True)
            )
        
        # Add disposition_notes if it doesn't exist
        if "disposition_notes" not in columns:
            op.add_column(
                "deal_briefs",
                sa.Column("disposition_notes", sa.Text(), nullable=True)
            )


def downgrade() -> None:
    """Remove disposition columns from deal_briefs table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if "deal_briefs" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("deal_briefs")]
        
        if "disposition_status" in columns:
            op.drop_column("deal_briefs", "disposition_status")
        
        if "disposition_notes" in columns:
            op.drop_column("deal_briefs", "disposition_notes")
