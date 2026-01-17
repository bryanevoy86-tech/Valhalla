"""Add telemetry_events table for audit trail

Revision ID: 001_telemetry_events
Revises: 
Create Date: 2025-12-25 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '001_telemetry_events'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'telemetry_events',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('leg', sa.String(50), nullable=False),
        sa.Column('reference_id', sa.String(255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('actor', sa.String(100), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_telemetry_events_event_type'), 'telemetry_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_telemetry_events_leg'), 'telemetry_events', ['leg'], unique=False)
    op.create_index(op.f('ix_telemetry_events_reference_id'), 'telemetry_events', ['reference_id'], unique=False)
    op.create_index(op.f('ix_telemetry_events_timestamp'), 'telemetry_events', ['timestamp'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_telemetry_events_timestamp'), table_name='telemetry_events')
    op.drop_index(op.f('ix_telemetry_events_reference_id'), table_name='telemetry_events')
    op.drop_index(op.f('ix_telemetry_events_leg'), table_name='telemetry_events')
    op.drop_index(op.f('ix_telemetry_events_event_type'), table_name='telemetry_events')
    op.drop_table('telemetry_events')
