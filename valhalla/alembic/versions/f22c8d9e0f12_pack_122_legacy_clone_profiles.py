"""pack_122_legacy_clone_profiles

Revision ID: f22c8d9e0f12
Revises: f21b7c8d9e01
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f22c8d9e0f12"
down_revision = "f21b7c8d9e01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "legacy_clone_profiles" not in inspect(bind).get_table_names():
        op.create_table(
            "legacy_clone_profiles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("min_monthly_income", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("min_reserve_months", sa.Float(), server_default=sa.text("2.0")),
            sa.Column("min_legacy_count", sa.Integer(), server_default=sa.text("1")),
            sa.Column("max_legacies", sa.Integer(), server_default=sa.text("100")),
            sa.Column("require_all_green_health", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("auto_clone_enabled", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("clones_per_batch", sa.Integer(), server_default=sa.text("1")),
            sa.Column("max_new_clones_per_year", sa.Integer(), server_default=sa.text("10")),
            sa.Column("notes", sa.Text()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_legacy_clone_profiles_id", "legacy_clone_profiles", ["id"], unique=False)
        op.create_index("ix_legacy_clone_profiles_name", "legacy_clone_profiles", ["name"], unique=True)


def downgrade():
    op.drop_index("ix_legacy_clone_profiles_name", table_name="legacy_clone_profiles")
    op.drop_index("ix_legacy_clone_profiles_id", table_name="legacy_clone_profiles")
    op.drop_table("legacy_clone_profiles")
