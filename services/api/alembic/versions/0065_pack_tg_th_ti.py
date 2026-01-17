"""PACK TG, TH, TI: Mental Load, Crisis, Financial Stress

Revision ID: 0065
Revises: 0064
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0065'
down_revision = '0064'
branch_labels = None
depends_on = None


def upgrade():
    # PACK TG: Mental Load Offloading Tables
    op.create_table(
        'mental_load_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('urgency_level', sa.Integer(), nullable=True),
        sa.Column('emotional_weight', sa.Integer(), nullable=True),
        sa.Column('action_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'mental_load_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_items', sa.Integer(), nullable=False),
        sa.Column('urgent_items', sa.Integer(), nullable=False),
        sa.Column('action_items', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK TH: Crisis Management Tables
    op.create_table(
        'crisis_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'crisis_action_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crisis_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('responsible_role', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['crisis_id'], ['crisis_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'crisis_log_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('crisis_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('event', sa.Text(), nullable=False),
        sa.Column('actions_taken', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['crisis_id'], ['crisis_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK TI: Financial Stress Early Warning Tables
    op.create_table(
        'financial_indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('threshold_type', sa.String(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'financial_stress_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('value_at_trigger', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['indicator_id'], ['financial_indicators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop PACK TI tables
    op.drop_table('financial_stress_events')
    op.drop_table('financial_indicators')

    # Drop PACK TH tables
    op.drop_table('crisis_log_entries')
    op.drop_table('crisis_action_steps')
    op.drop_table('crisis_profiles')

    # Drop PACK TG tables
    op.drop_table('mental_load_summaries')
    op.drop_table('mental_load_entries')
