"""pack_124_knowledge_sources

Revision ID: f24e0f123456
Revises: f23d9e0f1234
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f24e0f123456"
down_revision = "f23d9e0f1234"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "knowledge_sources" not in inspect(bind).get_table_names():
        op.create_table(
            "knowledge_sources",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("url", sa.String()),
            sa.Column("source_type", sa.String(), server_default=sa.text("'web'")),
            sa.Column("engines", sa.String(), nullable=False),
            sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("priority", sa.Integer(), server_default=sa.text("5")),
            sa.Column("notes", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        )
        op.create_index("ix_knowledge_sources_id", "knowledge_sources", ["id"], unique=False)
        op.create_index("ix_knowledge_sources_category", "knowledge_sources", ["category"], unique=False)
        op.create_index("ix_knowledge_sources_active", "knowledge_sources", ["active"], unique=False)


def downgrade():
    op.drop_index("ix_knowledge_sources_active", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_category", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_id", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
