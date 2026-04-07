"""arbitrage phase a (market feed + opportunities + sim ledger)

Revision ID: 20260203_arbitrage_phase_a
Revises: 20260201_merge_heads_final
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260203_arbitrage_phase_a"

# Chain: sandbox_visibility -> engine_readiness -> arbitrage_phase_a
down_revision = "20260203_engine_readiness"

branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "market_feed_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=True),
        sa.Column("venue", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="CAD"),
        sa.Column("url", sa.String(length=512), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "arbitrage_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("buy_source", sa.String(length=64), nullable=False),
        sa.Column("buy_price", sa.Float(), nullable=False),
        sa.Column("buy_url", sa.String(length=512), nullable=True),
        sa.Column("sell_source", sa.String(length=64), nullable=False),
        sa.Column("sell_price", sa.Float(), nullable=False),
        sa.Column("sell_url", sa.String(length=512), nullable=True),
        sa.Column("fees_estimate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("shipping_estimate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("gross_spread", sa.Float(), nullable=False),
        sa.Column("net_profit", sa.Float(), nullable=False),
        sa.Column("roi", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "arbitrage_sim_trades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("buy_price", sa.Float(), nullable=False),
        sa.Column("sell_price", sa.Float(), nullable=False),
        sa.Column("fees", sa.Float(), nullable=False, server_default="0"),
        sa.Column("shipping", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_profit", sa.Float(), nullable=False),
        sa.Column("roi", sa.Float(), nullable=False),
        sa.Column("linked_opportunity_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("arbitrage_sim_trades")
    op.drop_table("arbitrage_opportunities")
    op.drop_table("market_feed_events")
