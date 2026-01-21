"""Merge all 4 migration branches into single head

Revision ID: 20260121_merge_all_heads
Revises: ('20260113_offer_strategy', '85_god_case_rescan_fields', '9e9f0b8c7f91', 'v3_7_intake_notify')
Create Date: 2026-01-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260121_merge_all_heads'
down_revision = ('20260113_offer_strategy', '85_god_case_rescan_fields', '9e9f0b8c7f91', 'v3_7_intake_notify')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """This migration merges all 4 branches. No schema changes."""
    pass


def downgrade() -> None:
    """Downgrade not supported for merge migration."""
    pass
