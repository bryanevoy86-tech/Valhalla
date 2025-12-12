"""Pack 60: Tax Optimization & Write-Off Tracker"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "pack_60_tax_tracker"
down_revision = "0059_integrity_telemetry"
branch_labels = None
depends_on = None


def _table_exists(name: str, schema: str | None = None) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names(schema=schema)


def _index_exists(index_name: str, table_name: str, schema: str | None = None) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for ix in insp.get_indexes(table_name, schema=schema):
        if ix.get("name") == index_name:
            return True
    return False


def upgrade():
    # --- Pack 60: Tax Optimization & Write-Off Tracker ---

    if not _table_exists("expense_categories"):
        op.create_table(
            "expense_categories",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(64), unique=True, index=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("jurisdiction", sa.String(8), server_default="CAN"),
            sa.Column("notes", sa.Text)
        )

    if not _table_exists("writeoff_rules"):
        op.create_table(
            "writeoff_rules",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("version", sa.Integer, index=True),
            sa.Column("jurisdiction", sa.String(8), index=True),
            sa.Column("category_code", sa.String(64), index=True),
            sa.Column("params", postgresql.JSONB),
            sa.Column("risk_weight", sa.Float, default=0.3),
            sa.Column("active", sa.Boolean, server_default=sa.text("true"))
        )

    if not _table_exists("receipts"):
        op.create_table(
            "receipts",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), index=True),
            sa.Column("user_id", sa.String(64), index=True),
            sa.Column("vendor", sa.String(256)),
            sa.Column("total", sa.Numeric(12,2)),
            sa.Column("tax_paid", sa.Numeric(12,2)),
            sa.Column("currency", sa.String(8), server_default="CAD"),
            sa.Column("image_url", sa.String(512)),
            sa.Column("status", sa.String(32), server_default="uploaded"),
            sa.Column("raw_text", sa.Text),
            sa.Column("meta", postgresql.JSONB)
        )

    if not _table_exists("expense_items"):
        op.create_table(
            "expense_items",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("receipt_id", sa.BigInteger, sa.ForeignKey("receipts.id", ondelete="CASCADE"), index=True),
            sa.Column("line", sa.Integer),
            sa.Column("description", sa.String(512)),
            sa.Column("qty", sa.Float),
            sa.Column("unit_price", sa.Numeric(12,2)),
            sa.Column("line_total", sa.Numeric(12,2)),
            sa.Column("category_code", sa.String(64), index=True),
            sa.Column("business_use_pct", sa.Float, default=100.0),
            sa.Column("notes", sa.Text),
            sa.Column("meta", postgresql.JSONB)
        )

    if not _table_exists("audit_evidence"):
        op.create_table(
            "audit_evidence",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("receipt_id", sa.BigInteger, sa.ForeignKey("receipts.id", ondelete="CASCADE"), index=True),
            sa.Column("kind", sa.String(64)),
            sa.Column("url", sa.String(512)),
            sa.Column("hash", sa.String(64)),
            sa.Column("added_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )

    if not _table_exists("tax_risk_scores"):
        op.create_table(
            "tax_risk_scores",
            sa.Column("id", sa.BigInteger, primary_key=True),
            sa.Column("receipt_id", sa.BigInteger, sa.ForeignKey("receipts.id", ondelete="CASCADE"), index=True),
            sa.Column("score", sa.Float),
            sa.Column("explanation", sa.Text),
            sa.Column("calc_ts", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
        )


def downgrade():
    for t in ["tax_risk_scores","audit_evidence","expense_items","receipts","writeoff_rules","expense_categories"]:
        op.drop_table(t)
