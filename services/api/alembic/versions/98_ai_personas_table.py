"""Pack 100: add ai_personas table

Revision ID: 98_ai_personas_table
Revises: 97_error_logs_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "98_ai_personas_table"
down_revision = "97_error_logs_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "ai_personas" not in inspect(bind).get_table_names():
        op.create_table(
            "ai_personas",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("domain", sa.String(), nullable=False),
            sa.Column("status", sa.String(), server_default=sa.text("'active'")),
            sa.Column("description", sa.Text()),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("ai_personas")
