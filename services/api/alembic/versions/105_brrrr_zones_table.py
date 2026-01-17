"""Pack 112: add brrrr_zones table

Revision ID: 105_brrrr_zones_table
Revises: 104_legacy_performance_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "105_brrrr_zones_table"
down_revision = "104_legacy_performance_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "brrrr_zones" not in inspect(bind).get_table_names():
        op.create_table(
            "brrrr_zones",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("country", sa.String(), nullable=False),
            sa.Column("min_properties_before_team", sa.Integer(), server_default=sa.text("5")),
            sa.Column("current_property_count", sa.Integer(), server_default=sa.text("0")),
            sa.Column("currency", sa.String(), server_default=sa.text("'CAD'")),
            sa.Column("language", sa.String(), server_default=sa.text("'en'")),
            sa.Column("timezone", sa.String(), server_default=sa.text("'UTC'")),
            sa.Column("active", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("legal_profile_code", sa.String()),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("brrrr_zones")
