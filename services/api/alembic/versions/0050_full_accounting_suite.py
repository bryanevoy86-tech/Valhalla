"""Pack 50: Full Accounting Suite

Revision ID: 0050_full_accounting_suite
Revises: 0049_brrrr_zone_compliance
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0050_full_accounting_suite"
down_revision = "0049_brrrr_zone_compliance"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "acct_accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(24), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("type", sa.String(24), nullable=False),   # asset|liability|equity|income|expense
        sa.Column("currency", sa.String(8), nullable=False, server_default="CAD"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true"))
    )
    op.create_table(
        "acct_periods",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("label", sa.String(32), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("closed", sa.Boolean, nullable=False, server_default=sa.text("false"))
    )
    op.create_table(
        "acct_journal_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entry_date", sa.Date, nullable=False),
        sa.Column("memo", sa.String(256)),
        sa.Column("source", sa.String(64)),                 # stripe|receipt|manual|system
        sa.Column("source_ref", sa.String(128)),            # event id, receipt id, etc.
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "acct_journal_lines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entry_id", sa.Integer, sa.ForeignKey("acct_journal_entries.id", ondelete="CASCADE")),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("acct_accounts.id", ondelete="RESTRICT")),
        sa.Column("debit", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(14,2), nullable=False, server_default="0"),
        sa.Column("tax_code", sa.String(32)),               # e.g., GST, HST, VAT
        sa.Column("tag", sa.String(64))                     # optional analytics tag
    )
    op.create_index("ix_acct_journal_lines_entry", "acct_journal_lines", ["entry_id"]) 
    op.create_index("ix_acct_journal_lines_account", "acct_journal_lines", ["account_id"]) 

    op.create_table(
        "acct_tax_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),  # GST5, HST13, PST7, etc.
        sa.Column("rate_pct", sa.Float, nullable=False),
        sa.Column("applies_to", sa.String(24), nullable=False),         # income|expense|both
        sa.Column("jurisdiction", sa.String(24), nullable=True)         # CA-MB, CA-ON, etc.
    )
    op.create_table(
        "acct_tax_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), unique=True, nullable=False),  # meals, tools, vehicle, etc.
        sa.Column("risk_weight", sa.Float, nullable=False, server_default="0.5")
    )
    op.create_table(
        "acct_tax_mappings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("acct_accounts.id", ondelete="CASCADE")),
        sa.Column("tax_category_id", sa.Integer, sa.ForeignKey("acct_tax_categories.id", ondelete="CASCADE"))
    )
    op.create_index("ix_acct_tax_mappings_account", "acct_tax_mappings", ["account_id"]) 

    op.create_table(
        "acct_reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(24), nullable=False),                # pnl|tb|tax
        sa.Column("period_label", sa.String(32), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    op.create_table(
        "cra_bot_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("period_label", sa.String(32), nullable=False),
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"))
    )


def downgrade():
    op.drop_table("cra_bot_runs")
    op.drop_table("acct_reports")
    op.drop_index("ix_acct_tax_mappings_account", table_name="acct_tax_mappings")
    op.drop_table("acct_tax_mappings")
    op.drop_table("acct_tax_categories")
    op.drop_table("acct_tax_rules")
    op.drop_index("ix_acct_journal_lines_account", table_name="acct_journal_lines")
    op.drop_index("ix_acct_journal_lines_entry", table_name="acct_journal_lines")
    op.drop_table("acct_journal_lines")
    op.drop_table("acct_journal_entries")
    op.drop_table("acct_periods")
    op.drop_table("acct_accounts")
