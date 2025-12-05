"""0106_pack_r_governance_decisions

Revision ID: 0106_pack_r_governance_decisions
Revises: 0105_pack_q_audit_events
Create Date: 2025-12-05

PACK R: Governance Integration - Governance Decisions Table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0106_pack_r_governance_decisions'
down_revision = '0105_pack_q_audit_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create governance_decisions table for leadership decision tracking."""
    op.create_table(
        'governance_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subject_type', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index(op.f('ix_governance_decisions_id'), 'governance_decisions', ['id'], unique=False)
    op.create_index(op.f('ix_governance_decisions_subject_type'), 'governance_decisions', ['subject_type'], unique=False)
    op.create_index(op.f('ix_governance_decisions_subject_id'), 'governance_decisions', ['subject_id'], unique=False)
    op.create_index(op.f('ix_governance_decisions_role'), 'governance_decisions', ['role'], unique=False)
    op.create_index(op.f('ix_governance_decisions_action'), 'governance_decisions', ['action'], unique=False)
    op.create_index(op.f('ix_governance_decisions_is_final'), 'governance_decisions', ['is_final'], unique=False)
    
    # Composite index for subject lookups (most common query pattern)
    op.create_index(
        'ix_governance_decisions_subject',
        'governance_decisions',
        ['subject_type', 'subject_id'],
        unique=False
    )


def downgrade() -> None:
    """Drop governance_decisions table."""
    op.drop_index('ix_governance_decisions_subject', table_name='governance_decisions')
    op.drop_index(op.f('ix_governance_decisions_is_final'), table_name='governance_decisions')
    op.drop_index(op.f('ix_governance_decisions_action'), table_name='governance_decisions')
    op.drop_index(op.f('ix_governance_decisions_role'), table_name='governance_decisions')
    op.drop_index(op.f('ix_governance_decisions_subject_id'), table_name='governance_decisions')
    op.drop_index(op.f('ix_governance_decisions_subject_type'), table_name='governance_decisions')
    op.drop_index(op.f('ix_governance_decisions_id'), table_name='governance_decisions')
    op.drop_table('governance_decisions')
