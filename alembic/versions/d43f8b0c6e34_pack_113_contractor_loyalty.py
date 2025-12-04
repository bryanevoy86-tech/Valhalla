"""pack_113_contractor_loyalty

Revision ID: d43f8b0c6e34
Revises: c32f7a9b5d23
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "d43f8b0c6e34"
down_revision: Union[str, Sequence[str], None] = "c32f7a9b5d23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
        op.create_index("ix_contractor_ranks_code", "contractor_ranks", ["code"], unique=True)
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
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_contractor_loyalty_vaults_id", "contractor_loyalty_vaults", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_contractor_ranks_code", table_name="contractor_ranks")
    op.drop_index("ix_contractor_loyalty_vaults_id", table_name="contractor_loyalty_vaults")
    op.drop_table("contractor_loyalty_vaults")
    op.drop_table("contractor_ranks")
