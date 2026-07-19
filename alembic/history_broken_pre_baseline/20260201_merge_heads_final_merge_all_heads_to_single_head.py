"""merge all heads to single head

Revision ID: 20260201_merge_heads_final
Revises: 0068, v3_8_contracts, 20260121_merge_all_heads
Create Date: 2026-02-01 12:25:18.036435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260201_merge_heads_final'
down_revision: Union[str, Sequence[str], None] = ('0068', 'v3_8_contracts', '20260121_merge_all_heads')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
