"""create lead_intake_exec table for execution layer

Revision ID: 001_add_execution_columns_to_lead_intake
Revises: 
Create Date: 2026-04-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect

# revision identifiers, used by Alembic.
revision = '001_add_execution_columns_to_lead_intake'
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists"""
    try:
        bind = op.get_bind()
        inspector = inspect(bind)
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def upgrade() -> None:
    # Create lead_intake_exec table if it doesn't exist
    if not table_exists('lead_intake_exec'):
        op.create_table(
            'lead_intake_exec',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('raw_text', sa.Text(), nullable=False),
            sa.Column('source_type', sa.String(50), nullable=True, server_default='manual_entry'),
            sa.Column('status', sa.String(50), nullable=True, server_default='new'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.String(50), nullable=True, server_default='operators'),
            sa.Column('normalized_at', sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    # Drop table if it exists
    if table_exists('lead_intake_exec'):
        op.drop_table('lead_intake_exec')

