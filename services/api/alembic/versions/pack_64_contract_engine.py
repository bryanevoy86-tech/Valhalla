"""Pack 64: Contract Assembly 2.0 (Clause Library + Jurisdiction Templates)"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
import logging

revision = "pack_64_contract_engine"
down_revision = "pack_63_closer_engine"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


def _table_exists(bind, name: str) -> bool:
    return name in inspect(bind).get_table_names()


def upgrade():
    bind = op.get_bind()

    if _table_exists(bind, "clause_library"):
        logger.info("[migration 0064] clause_library already exists; skipping create_table")
    else:
        op.create_table(
            "clause_library",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(64), unique=True, index=True),
            sa.Column("jurisdiction", sa.String(16), index=True),
            sa.Column("title", sa.String(256)),
            sa.Column("body_md", sa.Text),
            sa.Column("variables", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("active", sa.Boolean, server_default=sa.text("true")),
        )

    if _table_exists(bind, "contract_templates"):
        logger.info("[migration 0064] contract_templates already exists; skipping create_table")
    else:
        op.create_table(
            "contract_templates",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("body", sa.Text, nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime,
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
                nullable=False,
            ),
        )

    if _table_exists(bind, "contract_instances"):
        logger.info("[migration 0064] contract_instances already exists; skipping create_table")
    else:
        op.create_table(
            "contract_instances",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("deal_id", sa.BigInteger, sa.ForeignKey("deals.id", ondelete="SET NULL"), index=True),
            sa.Column("template_id", sa.Integer, sa.ForeignKey("contract_templates.id", ondelete="SET NULL")),
            sa.Column("status", sa.String(32), index=True),
            sa.Column("pdf_url", sa.String(512)),
            sa.Column("variables", postgresql.JSONB),
            sa.Column("counterparty_email", sa.String(256)),
            sa.Column("counterparty_name", sa.String(256)),
            sa.Column("created_ts", sa.DateTime, server_default=sa.text("now()")),
            sa.Column("updated_ts", sa.DateTime, server_default=sa.text("now()")),
        )

    if _table_exists(bind, "contract_clauses_applied"):
        logger.info("[migration 0064] contract_clauses_applied already exists; skipping create_table")
    else:
        op.create_table(
            "contract_clauses_applied",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("contract_id", sa.BigInteger, sa.ForeignKey("contract_instances.id", ondelete="CASCADE"), index=True),
            sa.Column("clause_code", sa.String(64), index=True),
            sa.Column("resolved_text_md", sa.Text),
            sa.Column("position", sa.Integer),
        )

    if _table_exists(bind, "signature_status"):
        logger.info("[migration 0064] signature_status already exists; skipping create_table")
    else:
        op.create_table(
            "signature_status",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("contract_id", sa.BigInteger, sa.ForeignKey("contract_instances.id", ondelete="CASCADE"), index=True),
            sa.Column("signer_email", sa.String(256)),
            sa.Column("signer_name", sa.String(256)),
            sa.Column("role", sa.String(32)),
            sa.Column("status", sa.String(32)),
            sa.Column("updated_ts", sa.DateTime, server_default=sa.text("now()")),
        )


def downgrade():
    for t in ["signature_status", "contract_clauses_applied", "contract_instances", "contract_templates", "clause_library"]:
        op.drop_table(t)
