"""merge migration heads

Revision ID: 650836770c62
Revises: 20260422_add_brrrr_analysis, 20260506_001
Create Date: 2026-05-08 13:43:43.831982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '650836770c62'
down_revision: Union[str, Sequence[str], None] = ('20260422_add_brrrr_analysis', '20260506_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
