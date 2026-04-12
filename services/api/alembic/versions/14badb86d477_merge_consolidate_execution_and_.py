"""merge: consolidate execution and pipeline migration heads

Revision ID: 14badb86d477
Revises: 001_add_execution_columns_to_lead_intake, add_deal_pipeline_columns
Create Date: 2026-04-12 16:08:47.239439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14badb86d477'
down_revision: Union[str, Sequence[str], None] = ('001_add_execution_columns_to_lead_intake', 'add_deal_pipeline_columns')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
