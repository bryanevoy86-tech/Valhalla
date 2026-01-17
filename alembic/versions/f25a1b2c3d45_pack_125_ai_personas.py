"""pack_125_ai_personas

Revision ID: f25a1b2c3d45
Revises: f24e0f123456
Create Date: 2025-11-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "f25a1b2c3d45"
down_revision: Union[str, Sequence[str], None] = "f24e0f123456"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "ai_personas" not in inspector.get_table_names():
        op.create_table(
            "ai_personas",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("primary_domains", sa.String()),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("tone", sa.String(), server_default="neutral"),
            sa.Column("safety_level", sa.String(), server_default="high"),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )
        op.create_index("ix_ai_personas_name", "ai_personas", ["name"], unique=True)
        op.create_index("ix_ai_personas_code", "ai_personas", ["code"], unique=True)
        op.create_index("ix_ai_personas_active", "ai_personas", ["active"])


def downgrade() -> None:
    op.drop_index("ix_ai_personas_active", table_name="ai_personas")
    op.drop_index("ix_ai_personas_code", table_name="ai_personas")
    op.drop_index("ix_ai_personas_name", table_name="ai_personas")
    op.drop_table("ai_personas")
