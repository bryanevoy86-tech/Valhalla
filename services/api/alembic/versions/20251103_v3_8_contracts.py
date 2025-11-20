"""v3.8 - contract templates + records"""

Make table creation idempotent to avoid DuplicateTable errors if tables
already exist in the target database.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
import logging
import logging

revision = "v3_8_contracts"
down_revision = "v3_7_intake_notify"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "contract_templates" in tables:
        logger.info("[migration v3.8] contract_templates already exists; skipping create_table")
    else:
        op.create_table(
            "contract_templates",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("version", sa.String(length=40), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("body_text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )

    # Create records table if missing; FK references contract_templates either way.
    inspector = inspect(op.get_bind())
    tables = set(inspector.get_table_names())
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

def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
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
