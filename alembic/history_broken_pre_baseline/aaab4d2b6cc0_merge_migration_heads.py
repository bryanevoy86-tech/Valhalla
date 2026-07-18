"""merge migration heads

Revision ID: aaab4d2b6cc0
Revises: 106_contractor_loyalty_tables, pack_64_contract_engine
Create Date: 2025-12-12 10:20:14.174497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaab4d2b6cc0'
down_revision: Union[str, Sequence[str], None] = ('106_contractor_loyalty_tables', 'pack_64_contract_engine')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
