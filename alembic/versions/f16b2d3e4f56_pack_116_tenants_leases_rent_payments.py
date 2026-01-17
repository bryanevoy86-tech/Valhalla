"""pack_116_tenants_leases_rent_payments

Revision ID: f16b2d3e4f56
Revises: f15a1c2d3e45
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f16b2d3e4f56"
down_revision = "f15a1c2d3e45"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = inspect(bind).get_table_names()
    if "tenants" not in tables:
        op.create_table(
            "tenants",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("email", sa.String()),
            sa.Column("phone", sa.String()),
            sa.Column("notes", sa.String()),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_tenants_id", "tenants", ["id"], unique=False)
        op.create_index("ix_tenants_active", "tenants", ["active"], unique=False)
    if "leases" not in tables:
        op.create_table(
            "leases",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("rental_property_id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), nullable=False),
            sa.Column("start_date", sa.DateTime(), nullable=False),
            sa.Column("end_date", sa.DateTime()),
            sa.Column("rent_amount", sa.Float(), nullable=False),
            sa.Column("rent_currency", sa.String(), server_default=sa.text("'CAD'")),
            sa.Column("frequency", sa.String(), server_default=sa.text("'monthly'")),
            sa.Column("deposit_amount", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("status", sa.String(), server_default=sa.text("'active'")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_leases_id", "leases", ["id"], unique=False)
        op.create_index("ix_leases_status", "leases", ["status"], unique=False)
    if "rent_payments" not in tables:
        op.create_table(
            "rent_payments",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("lease_id", sa.Integer(), nullable=False),
            sa.Column("due_date", sa.DateTime(), nullable=False),
            sa.Column("amount_due", sa.Float(), nullable=False),
            sa.Column("amount_paid", sa.Float(), server_default=sa.text("0.0")),
            sa.Column("paid_date", sa.DateTime()),
            sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
            sa.Column("method", sa.String()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_rent_payments_id", "rent_payments", ["id"], unique=False)
        op.create_index("ix_rent_payments_status", "rent_payments", ["status"], unique=False)


def downgrade():
    op.drop_index("ix_rent_payments_status", table_name="rent_payments")
    op.drop_index("ix_rent_payments_id", table_name="rent_payments")
    op.drop_table("rent_payments")
    op.drop_index("ix_leases_status", table_name="leases")
    op.drop_index("ix_leases_id", table_name="leases")
    op.drop_table("leases")
    op.drop_index("ix_tenants_active", table_name="tenants")
    op.drop_index("ix_tenants_id", table_name="tenants")
    op.drop_table("tenants")
