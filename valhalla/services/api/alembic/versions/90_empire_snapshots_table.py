"""Pack 90: add empire_snapshots table

Revision ID: 90_empire_snapshots_table
Revises: 89_knowledge_sources_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "90_empire_snapshots_table"
down_revision = "89_knowledge_sources_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "empire_snapshots" not in inspect(bind).get_table_names():
        op.create_table(
            "empire_snapshots",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("snapshot_type", sa.String(), server_default=sa.text("'manual'")),
            sa.Column("summary_json", sa.Text(), nullable=False),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("empire_snapshots")
