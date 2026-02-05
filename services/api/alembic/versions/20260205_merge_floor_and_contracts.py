"""Final consolidation: make migration chain linear.

Revision ID: 20260205_final_consolidation
Revises: 20260205_contract_pipeline
Create Date: 2026-02-05

This migration consolidates all previous branches (arbitrage, sandbox visibility,
floor control, and contract pipeline) into a single linear migration chain.
Alembic can now resolve 'head' unambiguously.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260205_final_consolidation'
down_revision: Union[str, Sequence[str], None] = '20260205_contract_pipeline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - merge operation only, no schema changes."""
    pass


def downgrade() -> None:
    """Downgrade schema - merge operation only, no schema changes."""
    pass
