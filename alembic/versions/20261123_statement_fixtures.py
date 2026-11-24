"""Install the segregated treasury statement fixture journal."""
from alembic import op
import sqlalchemy as sa

revision = "20261123_statement_fixtures"
down_revision = "20261123_startup_intake"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("prime_statement_accounts",
                    sa.Column("account_key", sa.String(64), primary_key=True),
                    sa.Column("scope_key", sa.String(64), nullable=False),
                    sa.Column("currency", sa.String(3), nullable=False),
                    sa.Column("purpose", sa.String(18), nullable=False),
                    sa.Column("head_id", sa.Uuid()))
    op.create_table("prime_statement_imports",
                    sa.Column("id", sa.Uuid(), primary_key=True),
                    sa.Column("account_key", sa.String(64), nullable=False),
                    sa.Column("period_end", sa.Date(), nullable=False),
                    sa.Column("digest", sa.String(64), nullable=False),
                    sa.Column("payload", sa.JSON(), nullable=False))
    op.create_index("ix_statement_scope_account", "prime_statement_imports", ["account_key", "period_end"])
    op.create_table("prime_statement_entries",
                    sa.Column("key", sa.String(64), primary_key=True),
                    sa.Column("statement_id", sa.Uuid(), nullable=False))
    op.create_index("ix_prime_statement_entries_statement_id", "prime_statement_entries", ["statement_id"])


def downgrade():
    # Retain accounting evidence and replay protection.
    pass
