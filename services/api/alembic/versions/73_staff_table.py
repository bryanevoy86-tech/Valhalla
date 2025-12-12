"""add staff table

Revision ID: 73_staff_table
Revises: 85_god_case_rescan_fields
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '73_staff_table'
down_revision = '85_god_case_rescan_fields'
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade():
    if not _table_exists("staff"):
        op.create_table(
            "staff",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("region", sa.String()),
            sa.Column("pay_rate", sa.Float()),
            sa.Column("status", sa.String(), server_default="active"),
            sa.Column("reliability_score", sa.Float(), server_default="0.0"),
            sa.Column("skill_score", sa.Float(), server_default="0.0"),
            sa.Column("attitude_score", sa.Float(), server_default="0.0"),
            sa.Column("created_at", sa.DateTime())
        )
        op.create_index(op.f("ix_staff_full_name"), "staff", ["full_name"])
        op.create_index(op.f("ix_staff_role"), "staff", ["role"])


def downgrade():
    op.drop_index(op.f("ix_staff_role"), "staff")
    op.drop_index(op.f("ix_staff_full_name"), "staff")
    op.drop_table("staff")
