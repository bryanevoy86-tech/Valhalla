"""consolidate all migration heads

Revision ID: 5e5bb3b591a4
Revises: 0106_pack_r_governance, 20260205_ops_and_events, f2b00b1c2d4c, add_community_templates_and_logs_20260407, 9999_bootstrap_core, cl12_add_model_providers
Create Date: 2026-04-12 13:34:36.971495

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e5bb3b591a4'
down_revision: Union[str, Sequence[str], None] = ('0106_pack_r_governance', '20260205_ops_and_events', 'f2b00b1c2d4c', 'add_community_templates_and_logs_20260407', '9999_bootstrap_core', 'cl12_add_model_providers')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
