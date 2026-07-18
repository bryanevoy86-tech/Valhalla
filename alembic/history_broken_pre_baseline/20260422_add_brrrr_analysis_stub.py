"""Stub migration - this migration ID exists in production database but file was missing.

Revision ID: 20260422_add_brrrr_analysis
Revises: pack_65_buyer_match
Create Date: 2026-06-28

This is a placeholder migration file created to fix the alembic migration chain.
The migration ID '20260422_add_brrrr_analysis' existed in the production database
but had no corresponding file, causing alembic to fail.

This stub file allows alembic to proceed without errors.
"""

from alembic import op
import sqlalchemy as sa


revision = '20260422_add_brrrr_analysis'
down_revision = 'pack_65_buyer_match'
branch_labels = None
depends_on = None


def upgrade():
    """This is a stub migration - no changes to apply."""
    pass


def downgrade():
    """This is a stub migration - no changes to revert."""
    pass
