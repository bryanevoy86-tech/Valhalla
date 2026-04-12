"""add execution columns to lead_intake table

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


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        bind = op.get_bind()
        inspector = inspect(bind)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def upgrade() -> None:
    # Add raw_text column (NOT NULL with empty string server default)
    if not column_exists('lead_intake', 'raw_text'):
        op.add_column('lead_intake',
                      sa.Column('raw_text', sa.Text(),
                               nullable=False,
                               server_default=''))

    # Add source_type column
    if not column_exists('lead_intake', 'source_type'):
        op.add_column('lead_intake',
                      sa.Column('source_type', sa.String(50),
                               nullable=True,
                               server_default='manual_entry'))

    # Add created_by column
    if not column_exists('lead_intake', 'created_by'):
        op.add_column('lead_intake',
                      sa.Column('created_by', sa.String(50),
                               nullable=True,
                               server_default='operators'))

    # Add normalized_at column
    if not column_exists('lead_intake', 'normalized_at'):
        op.add_column('lead_intake',
                      sa.Column('normalized_at', sa.DateTime(),
                               nullable=True))


def downgrade() -> None:
    # Drop columns in reverse order if they exist
    if column_exists('lead_intake', 'normalized_at'):
        op.drop_column('lead_intake', 'normalized_at')
    if column_exists('lead_intake', 'created_by'):
        op.drop_column('lead_intake', 'created_by')
    if column_exists('lead_intake', 'source_type'):
        op.drop_column('lead_intake', 'source_type')
    if column_exists('lead_intake', 'raw_text'):
        op.drop_column('lead_intake', 'raw_text')
