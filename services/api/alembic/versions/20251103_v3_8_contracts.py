"""V3.8 – contracts migration

This migration manages contract-related tables.
It has been updated to be idempotent so it can safely run multiple times
in different environments without crashing on existing tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "v3_8_contracts"  # <-- keep whatever was already here
down_revision = "v3_7_intake_notify"        # <-- keep your existing value here
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # --- contract_templates table ---
    if "contract_templates" not in tables:
        op.create_table(
            "contract_templates",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("version", sa.String(length=40), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("body_text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )

    # --- contract_records table (if you have one in this migration) ---
    if "contract_records" not in tables:
        op.create_table(
            "contract_records",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "template_id",
                sa.Integer,
                sa.ForeignKey("contract_templates.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("filename", sa.String(length=200), nullable=False),
            sa.Column("context_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    # Drop in reverse order, guarded
    if "contract_records" in tables:
        op.drop_table("contract_records")

    if "contract_templates" in tables:
        op.drop_table("contract_templates")
