"""Pack 51: Legal Document Engine

Revision ID: 0051_legal_document_engine
Revises: 0050_full_accounting_suite
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0051_legal_document_engine"
down_revision = "0050_full_accounting_suite"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "legal_templates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("jurisdiction", sa.String(32), nullable=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true"))
    )
    op.create_table(
        "legal_template_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("template_id", sa.Integer, sa.ForeignKey("legal_templates.id", ondelete="CASCADE")),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("template_id", "version")
    )
    op.create_table(
        "legal_clauses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("jurisdiction", sa.String(32), nullable=True),
        sa.Column("body", sa.Text, nullable=False)
    )
    op.create_table(
        "legal_variables",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(64), unique=True, nullable=False),
        sa.Column("desc", sa.String(256), nullable=True),
        sa.Column("required", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("example", sa.String(256), nullable=True)
    )
    op.create_table(
        "legal_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("template_id", sa.Integer, sa.ForeignKey("legal_templates.id", ondelete="SET NULL")),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("rendered_body", sa.Text, nullable=False),
        sa.Column("variables_json", sa.Text, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("external_ref", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )


def downgrade():
    op.drop_table("legal_documents")
    op.drop_table("legal_variables")
    op.drop_table("legal_clauses")
    op.drop_table("legal_template_versions")
    op.drop_table("legal_templates")
