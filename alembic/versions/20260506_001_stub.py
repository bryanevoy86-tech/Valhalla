"""Stub migration - orphaned migration ID not found.

Revision ID: 20260506_001
Revises: 2f72b38af43b
Create Date: 2026-06-29

This is a placeholder migration file created to fix the alembic migration chain.
The migration ID '20260506_001' was referenced but had no corresponding file.

This stub file allows alembic to proceed without errors.
"""

from alembic import op
import sqlalchemy as sa


revision = '20260506_001'
down_revision = '2f72b38af43b'
branch_labels = None
depends_on = None


def upgrade():
    """This is a stub migration - no changes to apply."""
    pass


def downgrade():
    """This is a stub migration - no changes to revert."""
    pass
