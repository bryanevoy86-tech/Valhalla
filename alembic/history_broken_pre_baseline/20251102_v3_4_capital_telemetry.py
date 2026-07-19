"""
Alembic migration v3_4_capital_telemetry
Create telemetry_events and capital_intake tables.

Revision ID: v3_4_capital_telemetry
Revises: v3_4_embeddings
Create Date: 2025-01-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v3_4_capital_telemetry'
down_revision = 'v3_4_embeddings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection to check for table existence
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create telemetry_events table only if it doesn't exist
    if 'telemetry_events' not in existing_tables:
        op.create_table(
            'telemetry_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('kind', sa.String(length=80), nullable=False),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('meta_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_telemetry_events_kind'), 'telemetry_events', ['kind'], unique=False)
        op.create_index(op.f('ix_telemetry_events_created_at'), 'telemetry_events', ['created_at'], unique=False)
    
    # Create capital_intake table only if it doesn't exist
    if 'capital_intake' not in existing_tables:
        op.create_table(
            'capital_intake',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source', sa.String(length=120), nullable=False),
            sa.Column('currency', sa.String(length=12), nullable=False, server_default='CAD'),
            sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=False),
            sa.Column('note', sa.String(length=280), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_capital_intake_source'), 'capital_intake', ['source'], unique=False)
        op.create_index(op.f('ix_capital_intake_created_at'), 'capital_intake', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_capital_intake_created_at'), table_name='capital_intake')
    op.drop_index(op.f('ix_capital_intake_source'), table_name='capital_intake')
    op.drop_table('capital_intake')
    
    op.drop_index(op.f('ix_telemetry_events_created_at'), table_name='telemetry_events')
    op.drop_index(op.f('ix_telemetry_events_kind'), table_name='telemetry_events')
    op.drop_table('telemetry_events')
