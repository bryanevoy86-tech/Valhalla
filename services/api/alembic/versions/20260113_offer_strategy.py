"""offer strategy tables

Revision ID: 20260113_offer_strategy
Revises: 20260113_buyer_liquidity
"""
from alembic import op
import sqlalchemy as sa

revision = "20260113_offer_strategy"
down_revision = "20260113_buyer_liquidity"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "offer_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("province", sa.String(), nullable=False),
        sa.Column("market", sa.String(), nullable=False, server_default=sa.text("'ALL'")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("max_arv_multiplier", sa.Float(), nullable=False, server_default=sa.text("0.70")),
        sa.Column("default_assignment_fee", sa.Float(), nullable=False, server_default=sa.text("10000")),
        sa.Column("default_fees_buffer", sa.Float(), nullable=False, server_default=sa.text("2500")),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("province","market", name="uq_offer_policy_province_market"),
    )

    op.create_table(
        "offer_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("province", sa.String(), nullable=False),
        sa.Column("market", sa.String(), nullable=False, server_default=sa.text("'ALL'")),
        sa.Column("arv", sa.Float(), nullable=False),
        sa.Column("repairs", sa.Float(), nullable=False),
        sa.Column("fees_buffer", sa.Float(), nullable=False),
        sa.Column("mao", sa.Float(), nullable=False),
        sa.Column("recommended_offer", sa.Float(), nullable=False),
        sa.Column("comps_json", sa.Text(), nullable=True),
        sa.Column("assumptions_json", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

def downgrade():
    op.drop_table("offer_evidence")
    op.drop_table("offer_policy")
