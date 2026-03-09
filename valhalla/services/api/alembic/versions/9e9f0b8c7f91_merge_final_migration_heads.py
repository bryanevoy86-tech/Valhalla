"""merge final migration heads

Revision ID: 9e9f0b8c7f91
Revises: aaab4d2b6cc0, pack_65_buyer_match, v3_10_integrity_events
Create Date: 2025-12-12 11:47:36.309441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e9f0b8c7f91'
down_revision: Union[str, Sequence[str], None] = ('aaab4d2b6cc0', 'pack_65_buyer_match', 'v3_10_integrity_events')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
