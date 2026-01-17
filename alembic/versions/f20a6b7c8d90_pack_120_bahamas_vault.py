"""pack_120_bahamas_vault

Revision ID: f20a6b7c8d90
Revises: f19e5f6a7b89
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f20a6b7c8d90"
down_revision = "f19e5f6a7b89"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "bahamas_vault" not in inspect(bind).get_table_names():
        op.create_table(
            "bahamas_vault",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("current_balance", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("target_balance", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("min_resort_price", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("max_resort_price", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("percent_to_target", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("residency_ready", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("resort_search_active", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("notes", sa.Text()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_bahamas_vault_id", "bahamas_vault", ["id"], unique=False)
        op.create_index("ix_bahamas_vault_residency_ready", "bahamas_vault", ["residency_ready"], unique=False)


def downgrade():
    op.drop_index("ix_bahamas_vault_residency_ready", table_name="bahamas_vault")
    op.drop_index("ix_bahamas_vault_id", table_name="bahamas_vault")
    op.drop_table("bahamas_vault")
