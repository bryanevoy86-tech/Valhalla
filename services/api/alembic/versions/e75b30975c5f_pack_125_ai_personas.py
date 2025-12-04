"""pack_125_ai_personas

Revision ID: e75b30975c5f
Revises: 107_system_health_reports_table
Create Date: 2025-11-24 17:50:05.471507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e75b30975c5f'
down_revision: Union[str, Sequence[str], None] = '107_system_health_reports_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
