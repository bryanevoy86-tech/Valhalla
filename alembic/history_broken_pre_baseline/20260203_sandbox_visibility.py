"""SANDBOX visibility + approvals + human labels

Revision ID: 20260203_sandbox_visibility
Revises: 20260201_merge_heads_final
Create Date: 2026-02-03 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260203_sandbox_visibility'
down_revision = '20260201_merge_heads_final'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tables for SANDBOX visibility and approvals."""
    
    # sandbox_events table
    op.create_table(
        'sandbox_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('engine_name', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sandbox_events_engine', 'sandbox_events', ['engine_name'])
    op.create_index('idx_sandbox_events_created', 'sandbox_events', ['created_at'])

    # human_labels table
    op.create_table(
        'human_labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('engine_name', sa.String(length=64), nullable=False, server_default='wholesaling'),
        sa.Column('lead_ref', sa.String(length=128), nullable=True),
        sa.Column('label', sa.String(length=16), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_human_labels_engine', 'human_labels', ['engine_name'])
    op.create_index('idx_human_labels_lead', 'human_labels', ['lead_ref'])

    # pending_actions table
    op.create_table(
        'pending_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('engine_name', sa.String(length=64), nullable=False),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='PENDING'),
        sa.Column('target', sa.String(length=240), nullable=True),
        sa.Column('subject', sa.String(length=240), nullable=True),
        sa.Column('preview_text', sa.Text(), nullable=True),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pending_actions_status', 'pending_actions', ['status'])
    op.create_index('idx_pending_actions_engine', 'pending_actions', ['engine_name'])
    op.create_index('idx_pending_actions_created', 'pending_actions', ['created_at'])


def downgrade() -> None:
    """Drop SANDBOX tables."""
    op.drop_index('idx_pending_actions_created')
    op.drop_index('idx_pending_actions_engine')
    op.drop_index('idx_pending_actions_status')
    op.drop_table('pending_actions')
    
    op.drop_index('idx_human_labels_lead')
    op.drop_index('idx_human_labels_engine')
    op.drop_table('human_labels')
    
    op.drop_index('idx_sandbox_events_created')
    op.drop_index('idx_sandbox_events_engine')
    op.drop_table('sandbox_events')
