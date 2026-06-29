"""Expand alembic_version.version_num column to accommodate longer revision IDs

Revision ID: 20260428_expand_alembic_version
Revises: 20260408_community_schema_fix
Create Date: 2026-04-28

Alembic migration IDs can be longer than 32 characters, especially with descriptive names
like '0107_alter_contract_records_schema' (33 chars). This migration expands the column.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260428_expand_alembic_version'
down_revision = '20260408_community_schema_fix'
branch_labels = None
depends_on = None


def upgrade():
    """Expand alembic_version.version_num to accommodate longer revision IDs."""
    # Alter the alembic_version table's version_num column to be longer
    # Using raw SQL for PostgreSQL compatibility
    op.execute("""
        ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(256);
    """)


def downgrade():
    """Revert alembic_version.version_num back to VARCHAR(32)."""
    op.execute("""
        ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32);
    """)
