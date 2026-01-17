"""Add system_metadata table for PACK W

Revision ID: 20250920_add_system_metadata
Revises: 20250919_add_batch_and_limits
Create Date: 2025-09-20

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250920_add_system_metadata"
down_revision = "20250919_add_batch_and_limits"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(), nullable=False, server_default=sa.text("'1.0.0'")),
        sa.Column("backend_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_system_metadata_id", "id"),
    )


def downgrade():
    op.drop_table("system_metadata")
