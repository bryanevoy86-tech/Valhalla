"""merge heads: consolidate migration branches

Revision ID: 2e6ee01fce5e
Revises: va_intake_tables_raw
Create Date: 2026-05-19 17:47:40.099390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e6ee01fce5e'
down_revision: Union[str, Sequence[str], None] = ['0114', 'va_intake_tables_raw']
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
