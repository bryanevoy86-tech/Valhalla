"""pack_132_external_experts

Revision ID: f2ac0b1c2d48
Revises: f2ab0b1c2d47
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f2ac0b1c2d48"
down_revision: Union[str, Sequence[str], None] = "f2ab0b1c2d47"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "external_experts" not in inspector.get_table_names():
        op.create_table(
            "external_experts",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("firm", sa.String()),
            sa.Column("email", sa.String()),
            sa.Column("phone", sa.String()),
            sa.Column("specialty", sa.String(), nullable=False),
            sa.Column("jurisdiction", sa.String()),
            sa.Column("hourly_rate", sa.Float(), server_default="0.0"),
            sa.Column("preferred", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("last_contacted_at", sa.DateTime()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )
        op.create_index("ix_external_experts_specialty", "external_experts", ["specialty"])
        op.create_index("ix_external_experts_jurisdiction", "external_experts", ["jurisdiction"])
        op.create_index("ix_external_experts_preferred", "external_experts", ["preferred"])


def downgrade() -> None:
    op.drop_index("ix_external_experts_preferred", table_name="external_experts")
    op.drop_index("ix_external_experts_jurisdiction", table_name="external_experts")
    op.drop_index("ix_external_experts_specialty", table_name="external_experts")
    op.drop_table("external_experts")
