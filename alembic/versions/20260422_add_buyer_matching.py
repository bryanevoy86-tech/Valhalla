"""Add buyer candidates and deal-buyer matches tables

Revision ID: 20260422_add_buyer_matching
Revises: 20260422_add_audit_log
Create Date: 2026-04-22 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260422_add_buyer_matching'
down_revision = '20260422_add_audit_log'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create buyer_candidates and deal_buyer_matches tables."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Create buyer_candidates table if it doesn't exist
    if "buyer_candidates" not in inspector.get_table_names():
        op.create_table(
            "buyer_candidates",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("email", sa.String(160), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("buy_box", sa.Text, nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_buyer_candidates_name", "buyer_candidates", ["name"])
    
    # Create deal_buyer_matches table if it doesn't exist
    if "deal_buyer_matches" not in inspector.get_table_names():
        op.create_table(
            "deal_buyer_matches",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("deal_id", sa.Integer, nullable=False),
            sa.Column("buyer_id", sa.Integer, sa.ForeignKey("buyer_candidates.id"), nullable=False),
            sa.Column("match_status", sa.String(20), nullable=False, server_default="candidate"),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_deal_buyer_matches_deal_id", "deal_buyer_matches", ["deal_id"])
        op.create_index("ix_deal_buyer_matches_buyer_id", "deal_buyer_matches", ["buyer_id"])
        op.create_index("ix_deal_buyer_matches_status", "deal_buyer_matches", ["match_status"])


def downgrade() -> None:
    """Drop buyer_candidates and deal_buyer_matches tables."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Drop tables if they exist
    if "deal_buyer_matches" in inspector.get_table_names():
        op.drop_table("deal_buyer_matches")
    
    if "buyer_candidates" in inspector.get_table_names():
        op.drop_table("buyer_candidates")
