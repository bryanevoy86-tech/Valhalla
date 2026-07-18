"""PACK TJ, TK, TL: Kids Education, Life Timeline, Strategic Decisions

Revision ID: 0066
Revises: 0065
Create Date: 2024-01-01 00:00:00.000000

NOTE: This migration is idempotent - it safely handles cases where tables already exist
      (e.g., from earlier migrations, app initialization, or previous failed deployments).

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '0066'
down_revision = '0065'
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    """Check if a table exists in the current database."""
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    bind = op.get_bind()
    
    # PACK TJ: Kids Education & Development Tables
    if not _table_exists(bind, 'child_profiles'):
        op.create_table(
            'child_profiles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('age', sa.Integer(), nullable=True),
            sa.Column('interests', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if not _table_exists(bind, 'learning_plans'):
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

    if not _table_exists(bind, 'education_logs'):
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
    if not _table_exists(bind, 'life_events'):
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

    if not _table_exists(bind, 'life_milestones'):
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
    if not _table_exists(bind, 'strategic_decisions'):
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

    if not _table_exists(bind, 'decision_revisions'):
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

