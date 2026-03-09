"""bridge existing db revision 102_trust_status_table

Revision ID: 102_trust_status_table
Revises: fdc9b660a48f
Create Date: 2025-11-24
"""
from typing import Sequence, Union

revision: str = "102_trust_status_table"
down_revision: Union[str, Sequence[str], None] = "fdc9b660a48f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Bridge migration: original 102 content unavailable in this branch; assume applied.
    pass


def downgrade() -> None:
    # Do not attempt to remove prior 102 changes.
    pass
