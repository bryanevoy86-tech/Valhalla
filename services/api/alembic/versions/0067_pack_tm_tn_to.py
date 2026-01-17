"""Add philosophy, relationships, and daily rhythm tables

Revision ID: 0067
Revises: 0066
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0067'
down_revision = '0066'
branch_labels = None
depends_on = None


def upgrade():
    # PACK TM: Philosophy Records
    op.create_table(
        'philosophy_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('pillars', sa.Text(), nullable=True),
        sa.Column('mission_statement', sa.Text(), nullable=True),
        sa.Column('values', sa.Text(), nullable=True),
        sa.Column('rules_to_follow', sa.Text(), nullable=True),
        sa.Column('rules_to_never_break', sa.Text(), nullable=True),
        sa.Column('long_term_intent', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'empire_principles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('enforcement_level', sa.String(), nullable=False, server_default='soft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK TN: Relationships
    op.create_table(
        'relationship_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('relationship_type', sa.String(), nullable=True),
        sa.Column('user_trust_level', sa.Float(), nullable=True),
        sa.Column('boundaries', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'trust_event_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('event_description', sa.Text(), nullable=False),
        sa.Column('trust_change', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['profile_id'], ['relationship_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK TO: Daily Rhythm
    op.create_table(
        'daily_rhythm_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('wake_time', sa.String(), nullable=True),
        sa.Column('sleep_time', sa.String(), nullable=True),
        sa.Column('peak_focus_blocks', sa.JSON(), nullable=True),
        sa.Column('low_energy_blocks', sa.JSON(), nullable=True),
        sa.Column('family_blocks', sa.JSON(), nullable=True),
        sa.Column('personal_time_blocks', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'tempo_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profile_name', sa.String(), nullable=False),
        sa.Column('time_block', sa.String(), nullable=False),
        sa.Column('action_intensity', sa.String(), nullable=False),
        sa.Column('communication_style', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop PACK TO tables
    op.drop_table('tempo_rules')
    op.drop_table('daily_rhythm_profiles')

    # Drop PACK TN tables
    op.drop_table('trust_event_logs')
    op.drop_table('relationship_profiles')

    # Drop PACK TM tables
    op.drop_table('empire_principles')
    op.drop_table('philosophy_records')
