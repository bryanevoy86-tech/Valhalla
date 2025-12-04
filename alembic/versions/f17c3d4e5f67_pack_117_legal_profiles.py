"""pack_117_legal_profiles

Revision ID: f17c3d4e5f67
Revises: f16b2d3e4f56
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f17c3d4e5f67"
down_revision = "f16b2d3e4f56"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "legal_profiles" not in inspect(bind).get_table_names():
        op.create_table(
            "legal_profiles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(), nullable=False, unique=True),
            sa.Column("country", sa.String(), nullable=False),
            sa.Column("region", sa.String()),
            sa.Column("description", sa.Text()),
            sa.Column("requires_local_corp", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("allows_foreign_ownership", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("brrrr_refi_restricted", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("short_term_rental_restricted", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("eviction_strict", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("license_required", sa.Boolean(), server_default=sa.text("false")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_legal_profiles_id", "legal_profiles", ["id"], unique=False)
        op.create_index("ix_legal_profiles_code", "legal_profiles", ["code"], unique=True)
        op.create_index("ix_legal_profiles_country", "legal_profiles", ["country"], unique=False)


def downgrade():
    op.drop_index("ix_legal_profiles_country", table_name="legal_profiles")
    op.drop_index("ix_legal_profiles_code", table_name="legal_profiles")
    op.drop_index("ix_legal_profiles_id", table_name="legal_profiles")
    op.drop_table("legal_profiles")
