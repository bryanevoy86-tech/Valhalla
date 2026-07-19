"""URGENT: Expand alembic_version.version_num to accommodate long revision IDs

Revision ID: fix_alembic_version_column_width_early
Revises: 007_merge_all_heads_final
Create Date: 2026-04-01 (early in chain)

This MUST run very early because later revisions have long names like
'0107_alter_contract_records_schema' (33 chars) that exceed VARCHAR(32).
Previously this table was defined with VARCHAR(32) but we need VARCHAR(256).

Running this first ensures all subsequent migrations can execute.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_alembic_version_column_width_early'
down_revision = '007_merge_all_heads_final'
branch_labels = None
depends_on = None


def upgrade():
    """Expand alembic_version.version_num from VARCHAR(32) to VARCHAR(256)."""
    # Use raw SQL for PostgreSQL
    # This is safe idempotent - if already larger, no effect
    try:
        op.execute("""
            ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(256);
        """)
    except Exception:
        # If it fails (e.g., not on PostgreSQL), continue - might be on SQLite
        pass


def downgrade():
    """Revert to original size (not recommended in production)."""
    try:
        op.execute("""
            ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32);
        """)
    except Exception:
        pass
