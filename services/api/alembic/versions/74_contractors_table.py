"""add contractors table

Revision ID: 74_contractors_table
Revises: 73_staff_table
Create Date: 2025-11-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '74_contractors_table'
down_revision = '73_staff_table'
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def upgrade():
    if not _table_exists("contractors"):
        op.create_table(
            "contractors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("contact_person", sa.String()),
        sa.Column("region", sa.String()),
        sa.Column("loyalty_rank", sa.String(), server_default="Iron"),
        sa.Column("jobs_completed", sa.Integer(), server_default="0"),
        sa.Column("quality_score", sa.Float(), server_default="0.0"),
        sa.Column("speed_score", sa.Float(), server_default="0.0"),
        sa.Column("attitude_score", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime())
        )


def downgrade():
    op.drop_table("contractors")
