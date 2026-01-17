"""buyer liquidity graph

Revision ID: 20260113_buyer_liquidity
Revises: 20260113_followup_ladder
"""
from alembic import op
import sqlalchemy as sa

revision = "20260113_buyer_liquidity"
down_revision = "20260113_followup_ladder"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "buyer_liquidity_node",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("province", sa.String(), nullable=False),
        sa.Column("market", sa.String(), nullable=False, server_default=sa.text("'ALL'")),
        sa.Column("property_type", sa.String(), nullable=False, server_default=sa.text("'SFR'")),
        sa.Column("buyer_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("active_buyer_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_response_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_close_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("province","market","property_type", name="uq_liq_node"),
    )

    op.create_table(
        "buyer_feedback_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=False),
        sa.Column("market", sa.String(), nullable=False, server_default=sa.text("'ALL'")),
        sa.Column("property_type", sa.String(), nullable=False, server_default=sa.text("'SFR'")),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table("buyer_feedback_event")
    op.drop_table("buyer_liquidity_node")
