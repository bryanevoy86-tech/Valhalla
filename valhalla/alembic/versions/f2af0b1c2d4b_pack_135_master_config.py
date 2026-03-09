"""pack_135_master_config

Revision ID: f2af0b1c2d4b
Revises: f2ae0b1c2d4a
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f2af0b1c2d4b"
down_revision: Union[str, Sequence[str], None] = "f2ae0b1c2d4a"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "master_config" not in inspector.get_table_names():
        op.create_table(
            "master_config",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("config_key", sa.String(), nullable=False, unique=True),
            sa.Column("value_type", sa.String(), nullable=False, server_default="string"),
            sa.Column("value_string", sa.Text()),
            sa.Column("value_float", sa.Float()),
            sa.Column("value_int", sa.Integer()),
            sa.Column("value_bool", sa.Boolean()),
            sa.Column("value_json", sa.Text()),
            sa.Column("description", sa.Text()),
            sa.Column("ai_mutable", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )
        op.create_index("ix_master_config_key", "master_config", ["config_key"], unique=True)
        op.create_index("ix_master_config_ai_mutable", "master_config", ["ai_mutable"])


def downgrade() -> None:
    op.drop_index("ix_master_config_ai_mutable", table_name="master_config")
    op.drop_index("ix_master_config_key", table_name="master_config")
    op.drop_table("master_config")
