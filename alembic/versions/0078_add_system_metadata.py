"""0078 add system metadata

Revision ID: 0078
Revises: 0077
Create Date: 2025-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0078"
down_revision = "0077"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(), nullable=False, server_default="1.0.0"),
        sa.Column("backend_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_system_metadata_id", "id"),
    )


def downgrade() -> None:
    op.drop_table("system_metadata")
