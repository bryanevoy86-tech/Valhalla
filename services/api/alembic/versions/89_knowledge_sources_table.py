"""Pack 89: add knowledge_sources table

Revision ID: 89_knowledge_sources_table
Revises: 88_training_jobs_table
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "89_knowledge_sources_table"
down_revision = "88_training_jobs_table"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "knowledge_sources" not in inspect(bind).get_table_names():
        op.create_table(
            "knowledge_sources",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("source_type", sa.String(), nullable=False),
            sa.Column("url", sa.String()),
            sa.Column("category", sa.String()),
            sa.Column("priority", sa.Integer(), server_default="10"),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
        )


def downgrade():
    op.drop_table("knowledge_sources")
