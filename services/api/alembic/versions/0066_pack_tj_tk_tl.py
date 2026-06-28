"""PACK TJ, TK, TL: Kids Education, Life Timeline, Strategic Decisions

Revision ID: 0066
Revises: 0065
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0066'
down_revision = '0065'
branch_labels = None
depends_on = None


def upgrade():
    # PACK TJ: Kids Education & Development Tables
    op.create_table(
        'child_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('interests', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'learning_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('timeframe', sa.String(), nullable=False),
        sa.Column('goals', sa.Text(), nullable=True),
        sa.Column('activities', sa.Text(), nullable=True),
        sa.Column('parent_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'education_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('completed_activities', sa.Text(), nullable=True),
        sa.Column('highlights', sa.Text(), nullable=True),
        sa.Column('parent_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK TK: Life Timeline & Milestones Tables
    op.create_table(
        'life_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('impact_level', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'life_milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('milestone_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK TL: Strategic Decision Archive Tables
    op.create_table(
        'strategic_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('alternatives_considered', sa.Text(), nullable=True),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('expected_outcome', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'decision_revisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('decision_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('reason_for_revision', sa.Text(), nullable=False),
        sa.Column('what_changed', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['decision_id'], ['strategic_decisions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop PACK TL tables
    op.drop_table('decision_revisions')
    op.drop_table('strategic_decisions')

    # Drop PACK TK tables
    op.drop_table('life_milestones')
    op.drop_table('life_events')

    # Drop PACK TJ tables
    op.drop_table('education_logs')
    op.drop_table('learning_plans')
    op.drop_table('child_profiles')
