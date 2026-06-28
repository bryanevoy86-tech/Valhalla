"""add heimdall persistence tables

Revision ID: 0114
Revises: 0113
Create Date: 2026-05-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0114'
down_revision = '0113'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create heimdall_deals table
    op.create_table(
        'heimdall_deals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('property_address', sa.String(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('state_history', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heimdall_deals_state', 'heimdall_deals', ['state'])
    op.create_index('ix_heimdall_deals_property_address', 'heimdall_deals', ['property_address'])
    op.create_index('ix_heimdall_deals_id', 'heimdall_deals', ['id'])

    # Create heimdall_buyers table
    op.create_table(
        'heimdall_buyers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heimdall_buyers_name', 'heimdall_buyers', ['name'])
    op.create_index('ix_heimdall_buyers_id', 'heimdall_buyers', ['id'])

    # Create heimdall_tasks table
    op.create_table(
        'heimdall_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('deal_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('priority', sa.String(), nullable=True),
        sa.Column('owner_role', sa.String(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heimdall_tasks_deal_id', 'heimdall_tasks', ['deal_id'])
    op.create_index('ix_heimdall_tasks_status', 'heimdall_tasks', ['status'])
    op.create_index('ix_heimdall_tasks_id', 'heimdall_tasks', ['id'])

    # Create heimdall_approvals table
    op.create_table(
        'heimdall_approvals',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('deal_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('approval_type', sa.String(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heimdall_approvals_deal_id', 'heimdall_approvals', ['deal_id'])
    op.create_index('ix_heimdall_approvals_status', 'heimdall_approvals', ['status'])
    op.create_index('ix_heimdall_approvals_id', 'heimdall_approvals', ['id'])

    # Create heimdall_messages table
    op.create_table(
        'heimdall_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('deal_id', sa.String(), nullable=True),
        sa.Column('recipient_type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_heimdall_messages_deal_id', 'heimdall_messages', ['deal_id'])
    op.create_index('ix_heimdall_messages_status', 'heimdall_messages', ['status'])
    op.create_index('ix_heimdall_messages_id', 'heimdall_messages', ['id'])


def downgrade() -> None:
    op.drop_table('heimdall_messages')
    op.drop_table('heimdall_approvals')
    op.drop_table('heimdall_tasks')
    op.drop_table('heimdall_buyers')
    op.drop_table('heimdall_deals')
