"""Add VA intake tables

Revision ID: 20260506_001
Revises: 20260422_002
Create Date: 2026-05-06 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260506_001'
down_revision = '20260422_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Create va_leads table if it doesn't exist
    if "va_leads" not in inspector.get_table_names():
        op.create_table(
            'va_leads',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_platform', sa.String(60), nullable=False),
            sa.Column('source_type', sa.String(60), nullable=False),
            sa.Column('source_url', sa.String(500), nullable=True),
            sa.Column('address', sa.String(240), nullable=True),
            sa.Column('city', sa.String(120), nullable=True),
            sa.Column('province', sa.String(10), nullable=True),
            sa.Column('seller_name', sa.String(160), nullable=True),
            sa.Column('seller_phone', sa.String(40), nullable=True),
            sa.Column('seller_email', sa.String(160), nullable=True),
            sa.Column('asking_price', sa.Numeric(15, 2), nullable=True),
            sa.Column('raw_text', sa.Text(), nullable=True),
            sa.Column('va_notes', sa.Text(), nullable=True),
            sa.Column('strategy_fit', sa.String(60), nullable=True),
            sa.Column('submitted_by', sa.String(80), nullable=False, server_default='va'),
            sa.Column('heimdall_score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('risk_level', sa.String(20), nullable=False, server_default='high'),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('recommended_action', sa.String(255), nullable=True),
            sa.Column('status', sa.String(60), nullable=False, server_default='pending'),
            sa.Column('stage', sa.String(60), nullable=False, server_default='intake'),
            sa.Column('deal_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_va_leads_created_at', 'va_leads', ['created_at'])
        op.create_index('ix_va_leads_deal_id', 'va_leads', ['deal_id'])

    # Create va_approval_queue table if it doesn't exist
    if "va_approval_queue" not in inspector.get_table_names():
        op.create_table(
            'va_approval_queue',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('entity_type', sa.String(60), nullable=False, server_default='lead'),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('va_lead_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(60), nullable=False, server_default='pending'),
            sa.Column('recommended_action', sa.String(255), nullable=True),
            sa.Column('heimdall_score', sa.Integer(), nullable=True),
            sa.Column('risk_level', sa.String(20), nullable=True),
            sa.Column('assigned_to', sa.String(80), nullable=True),
            sa.Column('approved_by', sa.String(80), nullable=True),
            sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('denied_by', sa.String(80), nullable=True),
            sa.Column('denied_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('denial_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_va_approval_queue_entity_id', 'va_approval_queue', ['entity_id'])
        op.create_index('ix_va_approval_queue_va_lead_id', 'va_approval_queue', ['va_lead_id'])
        op.create_index('ix_va_approval_queue_created_at', 'va_approval_queue', ['created_at'])

    # Create va_audit_logs table if it doesn't exist
    if "va_audit_logs" not in inspector.get_table_names():
        op.create_table(
            'va_audit_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('actor', sa.String(80), nullable=False),
            sa.Column('action', sa.String(100), nullable=False),
            sa.Column('entity_type', sa.String(60), nullable=False, server_default='va_lead'),
            sa.Column('entity_id', sa.Integer(), nullable=False),
            sa.Column('details', sa.Text(), nullable=True),
            sa.Column('old_value', sa.Text(), nullable=True),
            sa.Column('new_value', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='success'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_va_audit_logs_entity_id', 'va_audit_logs', ['entity_id'])
        op.create_index('ix_va_audit_logs_created_at', 'va_audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_va_audit_logs_created_at', table_name='va_audit_logs')
    op.drop_index('ix_va_audit_logs_entity_id', table_name='va_audit_logs')
    op.drop_table('va_audit_logs')
    
    op.drop_index('ix_va_approval_queue_created_at', table_name='va_approval_queue')
    op.drop_index('ix_va_approval_queue_va_lead_id', table_name='va_approval_queue')
    op.drop_index('ix_va_approval_queue_entity_id', table_name='va_approval_queue')
    op.drop_table('va_approval_queue')
    
    op.drop_index('ix_va_leads_deal_id', table_name='va_leads')
    op.drop_index('ix_va_leads_created_at', table_name='va_leads')
    op.drop_table('va_leads')
