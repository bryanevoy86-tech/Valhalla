"""Merge floor control plane and contract pipeline heads.

Revision ID: 20260205_merge_floor_and_contracts
Revises: 20260205_add_floor_control_plane, 20260205_contract_pipeline
Create Date: 2026-02-05

This merge migration unifies the two separate branches:
- Floor Control Plane (20260205_add_floor_control_plane)
- Contract Pipeline (20260205_contract_pipeline)

Both migrations are now resolved into a single linear migration chain.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260205_merge_floor_and_contracts'
down_revision: Union[str, Sequence[str], None] = ('20260205_add_floor_control_plane', '20260205_contract_pipeline')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - merge operation only, no schema changes."""
    pass


def downgrade() -> None:
    """Downgrade schema - merge operation only, no schema changes."""
    pass
