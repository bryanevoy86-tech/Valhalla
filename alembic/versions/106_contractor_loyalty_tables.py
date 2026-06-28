"""Pack 113: add contractor loyalty tables

Revision ID: 106_contractor_loyalty_tables
Revises: 105_brrrr_zones_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "106_contractor_loyalty_tables"
down_revision = "105_brrrr_zones_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    if "contractor_ranks" not in insp.get_table_names():
        op.create_table(
            "contractor_ranks",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("min_score", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("max_score", sa.Float(), server_default=sa.text("100.0")),
            sa.Column("perks", sa.Text()),
        )
    if "contractor_loyalty_vaults" not in insp.get_table_names():
        op.create_table(
            "contractor_loyalty_vaults",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("contractor_id", sa.Integer(), nullable=False),
            sa.Column("contractor_name", sa.String(), nullable=False),
            sa.Column("rank_code", sa.String(), nullable=False),
            sa.Column("loyalty_score", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("vault_balance", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("jv_eligible", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("contractor_loyalty_vaults")
    op.drop_table("contractor_ranks")
