"""pack_129_governance_settings

Revision ID: f29e5f6a7b89
Revises: f28d4e5f6a78
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f29e5f6a7b89"
down_revision: Union[str, Sequence[str], None] = "f28d4e5f6a78"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "governance_settings" not in inspector.get_table_names():
        op.create_table(
            "governance_settings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("mode", sa.String(), server_default="hybrid"),
            sa.Column("max_auto_transfer", sa.Float(), server_default="1000.0"),
            sa.Column("max_auto_contract_commit", sa.Float(), server_default="5000.0"),
            sa.Column("require_approval_new_zone", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("require_approval_new_legacy", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("require_approval_large_hire", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("shield_always_on", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("log_all_decisions", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("updated_at", sa.DateTime()),
            sa.Column("created_at", sa.DateTime()),
        )
        op.create_index("ix_governance_settings_name", "governance_settings", ["name"], unique=True)
        op.create_index("ix_governance_settings_mode", "governance_settings", ["mode"])


def downgrade() -> None:
    op.drop_index("ix_governance_settings_mode", table_name="governance_settings")
    op.drop_index("ix_governance_settings_name", table_name="governance_settings")
    op.drop_table("governance_settings")
