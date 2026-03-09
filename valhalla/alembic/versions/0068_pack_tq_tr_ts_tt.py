"""Create PACK TQ, TR, TS, TT tables for security orchestration.

Revision ID: 0068
Revises: 0067
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0068'
down_revision = '0067'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK TQ: Security Policy tables
    op.create_table(
        'security_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('default_mode', sa.String(), nullable=False, server_default='normal'),
        sa.Column('auto_elevate', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('auto_lockdown', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('max_failed_auth', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_scan_events', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'blocked_entities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_blocked_entities_entity_type', 'entity_type'),
        sa.Index('ix_blocked_entities_value', 'value'),
        sa.Index('ix_blocked_entities_active', 'active')
    )
    
    # PACK TR: Security Action tables
    op.create_table(
        'security_action_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('requested_by', sa.String(), nullable=False),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_security_action_requests_status', 'status'),
        sa.Index('ix_security_action_requests_created_at', 'created_at')
    )
    
    # PACK TS: Honeypot tables
    op.create_table(
        'honeypot_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('api_key', sa.String(), nullable=False, unique=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('honeypot_type', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_honeypot_instances_name', 'name'),
        sa.Index('ix_honeypot_instances_api_key', 'api_key'),
        sa.Index('ix_honeypot_instances_active', 'active')
    )
    
    op.create_table(
        'honeypot_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('honeypot_id', sa.Integer(), nullable=False),
        sa.Column('source_ip', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('detected_threat', sa.String(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['honeypot_id'], ['honeypot_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_honeypot_events_honeypot_id', 'honeypot_id'),
        sa.Index('ix_honeypot_events_source_ip', 'source_ip'),
        sa.Index('ix_honeypot_events_processed', 'processed')
    )


def downgrade() -> None:
    op.drop_table('honeypot_events')
    op.drop_table('honeypot_instances')
    op.drop_table('security_action_requests')
    op.drop_table('blocked_entities')
    op.drop_table('security_policies')
