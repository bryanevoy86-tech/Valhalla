"""add children, chores, coin ledger tables (conditional create to avoid duplicates)

Revision ID: 83_children_hub_tables
Revises: 82_queen_streams_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "83_children_hub_tables"
down_revision = "82_queen_streams_table"
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("children"):
        op.create_table(
            "children",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("nickname", sa.String()),
            sa.Column("status", sa.String(), server_default="active"),
            sa.Column("created_at", sa.DateTime()),
        )

    if not inspector.has_table("chores"):
        op.create_table(
            "chores",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("child_id", sa.Integer(), sa.ForeignKey("children.id"), nullable=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.String()),
            sa.Column("coin_value", sa.Float(), server_default="0.0"),
            sa.Column("frequency", sa.String(), server_default="ad-hoc"),
            sa.Column("status", sa.String(), server_default="active"),
            sa.Column("created_at", sa.DateTime()),
        )

    if not inspector.has_table("coin_ledger"):
        op.create_table(
            "coin_ledger",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("child_id", sa.Integer(), sa.ForeignKey("children.id"), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("reason", sa.String()),
            sa.Column("entry_type", sa.String(), server_default="earn"),
            sa.Column("created_at", sa.DateTime()),
        )

def downgrade():
    # Drop in reverse order if exists
    op.execute("DROP TABLE IF EXISTS coin_ledger CASCADE")
    op.execute("DROP TABLE IF EXISTS chores CASCADE")
    op.execute("DROP TABLE IF EXISTS children CASCADE")
