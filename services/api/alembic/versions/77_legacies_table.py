"""add legacies table

Revision ID: 77_legacies_table
Revises: 76_trusts_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

revision = "77_legacies_table"
down_revision = "76_trusts_table"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "legacies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("readiness_score", sa.Integer(), server_default="0"),
        sa.Column("auto_clone_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_clone_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime())
    )

def downgrade():
    op.drop_table("legacies")
