"""0105_pack_q_audit_events

Revision ID: 0105_pack_q_audit_events
Revises: 0104_document_routing
Create Date: 2025-12-05

PACK Q: Internal Auditor - Audit Events Table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '0105_pack_q_audit_events'
down_revision = '0104_document_routing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_events table for operational compliance tracking."""
    # Check if table already exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    
    if 'audit_events' in tables:
        print("INFO: audit_events table already exists, skipping creation")
        return
    
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('professional_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index(op.f('ix_audit_events_id'), 'audit_events', ['id'], unique=False)
    op.create_index(op.f('ix_audit_events_deal_id'), 'audit_events', ['deal_id'], unique=False)
    op.create_index(op.f('ix_audit_events_professional_id'), 'audit_events', ['professional_id'], unique=False)
    op.create_index(op.f('ix_audit_events_code'), 'audit_events', ['code'], unique=False)
    op.create_index(op.f('ix_audit_events_severity'), 'audit_events', ['severity'], unique=False)
    op.create_index(op.f('ix_audit_events_is_resolved'), 'audit_events', ['is_resolved'], unique=False)


def downgrade() -> None:
    """Drop audit_events table."""
    op.drop_index(op.f('ix_audit_events_is_resolved'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_severity'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_code'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_professional_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_deal_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_id'), table_name='audit_events')
    op.drop_table('audit_events')
