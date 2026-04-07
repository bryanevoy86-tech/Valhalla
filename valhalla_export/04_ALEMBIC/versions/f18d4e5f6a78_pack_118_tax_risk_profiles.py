"""pack_118_tax_risk_profiles

Revision ID: f18d4e5f6a78
Revises: f17c3d4e5f67
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f18d4e5f6a78"
down_revision = "f17c3d4e5f67"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "tax_risk_profiles" not in inspect(bind).get_table_names():
        op.create_table(
            "tax_risk_profiles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("jurisdiction", sa.String(), nullable=False, server_default=sa.text("'CRA'")),
            sa.Column("risk_level", sa.Float(), server_default=sa.text("0.5")),
            sa.Column("meals_percent_cap", sa.Float(), server_default=sa.text("0.10")),
            sa.Column("vehicle_percent_cap", sa.Float(), server_default=sa.text("0.30")),
            sa.Column("home_office_percent_cap", sa.Float(), server_default=sa.text("0.20")),
            sa.Column("travel_percent_cap", sa.Float(), server_default=sa.text("0.15")),
            sa.Column("auto_flag_red", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_tax_risk_profiles_id", "tax_risk_profiles", ["id"], unique=False)
        op.create_index("ix_tax_risk_profiles_name", "tax_risk_profiles", ["name"], unique=True)
        op.create_index("ix_tax_risk_profiles_jurisdiction", "tax_risk_profiles", ["jurisdiction"], unique=False)


def downgrade():
    op.drop_index("ix_tax_risk_profiles_jurisdiction", table_name="tax_risk_profiles")
    op.drop_index("ix_tax_risk_profiles_name", table_name="tax_risk_profiles")
    op.drop_index("ix_tax_risk_profiles_id", table_name="tax_risk_profiles")
    op.drop_table("tax_risk_profiles")
