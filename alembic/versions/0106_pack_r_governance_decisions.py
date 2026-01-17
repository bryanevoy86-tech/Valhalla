"""pack_r_governance_decisions

Revision ID: 0106_pack_r_governance
Revises: f2af0b1c2d4b
Create Date: 2025-12-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "0106_pack_r_governance"
down_revision: Union[str, Sequence[str], None] = "f2af0b1c2d4b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if "governance_decisions" not in inspector.get_table_names():
        op.create_table(
            "governance_decisions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("subject_type", sa.String(), nullable=False),
            sa.Column("subject_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        
        # Indexes for query performance
        op.create_index("ix_governance_decisions_id", "governance_decisions", ["id"], unique=False)
        op.create_index("ix_governance_decisions_subject", "governance_decisions", ["subject_type", "subject_id"], unique=False)
        op.create_index("ix_governance_decisions_role", "governance_decisions", ["role"], unique=False)
        op.create_index("ix_governance_decisions_action", "governance_decisions", ["action"], unique=False)
        op.create_index("ix_governance_decisions_is_final", "governance_decisions", ["is_final"], unique=False)
        op.create_index("ix_governance_decisions_created_at", "governance_decisions", ["created_at"], unique=False)
        op.create_index("ix_governance_decisions_subject_final", "governance_decisions", ["subject_type", "subject_id", "is_final"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_governance_decisions_subject_final", table_name="governance_decisions")
    op.drop_index("ix_governance_decisions_created_at", table_name="governance_decisions")
    op.drop_index("ix_governance_decisions_is_final", table_name="governance_decisions")
    op.drop_index("ix_governance_decisions_action", table_name="governance_decisions")
    op.drop_index("ix_governance_decisions_role", table_name="governance_decisions")
    op.drop_index("ix_governance_decisions_subject", table_name="governance_decisions")
    op.drop_index("ix_governance_decisions_id", table_name="governance_decisions")
    op.drop_table("governance_decisions")
