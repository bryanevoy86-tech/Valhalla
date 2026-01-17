"""Pack 87: add global_settings table

Revision ID: 87_global_settings_table
Revises: 86_system_health_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "87_global_settings_table"
down_revision = "86_system_health_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "global_settings" not in inspect(bind).get_table_names():
        op.create_table(
            "global_settings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("key", sa.String(), nullable=False, unique=True),
            sa.Column("value", sa.String(), nullable=False),
            sa.Column("category", sa.String(), server_default=sa.text("'core'")),
            sa.Column("description", sa.Text()),
            sa.Column("is_feature_flag", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("global_settings")
