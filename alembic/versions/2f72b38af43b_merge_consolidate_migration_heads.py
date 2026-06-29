"""merge: consolidate migration heads

Revision ID: 2f72b38af43b
Revises: 20260408_community_schema_fix, cleanup_orphaned_alembic_version_records
Create Date: 2026-06-28 22:55:06.598847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f72b38af43b'
down_revision: Union[str, Sequence[str], None] = ('20260408_community_schema_fix', 'cleanup_orphaned_alembic_version_records')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
