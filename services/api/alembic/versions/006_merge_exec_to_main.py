"""merge execution migrations into main chain

Revision ID: 006_merge_exec_to_main
Revises: 005_exec_remaining_tables, 20260330_add_updated_ts_to_deals
Create Date: 2026-04-13 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_merge_exec_to_main'
down_revision = ['005_exec_remaining_tables', '20260330_add_updated_ts_to_deals']
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge execution layer migrations with other heads"""
    pass


def downgrade() -> None:
    """No-op downgrade"""
    pass
