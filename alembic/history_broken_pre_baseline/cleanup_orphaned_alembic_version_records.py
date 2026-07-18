"""Clean up orphaned alembic_version records that don't have migration files.

Revision ID: cleanup_orphaned_alembic_version_records
Revises: pack_65_buyer_match
Create Date: 2026-06-28

This migration removes entries from alembic_version table where the
migration file no longer exists. This can happen due to migration rebase,
squashing, or deletion of migration files.

Specifically, this removes the orphaned '20260422_add_brrrr_analysis' record
that exists in production but has no corresponding migration file.
"""

from alembic import op
import sqlalchemy as sa


revision = 'cleanup_orphaned_alembic_version_records'
down_revision = '20260422_add_brrrr_analysis'
branch_labels = None
depends_on = None


def upgrade():
    """Remove orphaned migration records."""
    # This is a data-only migration that directly modifies alembic_version
    # We're removing entries that don't have corresponding migration files
    
    connection = op.get_bind()
    
    # List of orphaned migration IDs to clean up
    orphaned_ids = [
        '20260422_add_brrrr_analysis',
    ]
    
    for orphaned_id in orphaned_ids:
        connection.execute(
            sa.text("""
                DELETE FROM alembic_version 
                WHERE version_num = :id
            """),
            {'id': orphaned_id}
        )
        print(f"Cleaned up orphaned migration: {orphaned_id}")


def downgrade():
    """This is a data-only cleanup migration and cannot be safely reversed."""
    # This migration is data-destructive and cannot be downgraded
    # If you need to downgrade, you'll need to restore from a backup
    pass
