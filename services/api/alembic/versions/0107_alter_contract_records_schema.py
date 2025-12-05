"""0107_alter_contract_records_schema

Revision ID: 0107_alter_contract_records_schema
Revises: 0106_pack_r_governance_decisions
Create Date: 2025-12-05

Alter contract_records table to match PACK N schema
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '0107_alter_contract_records_schema'
down_revision = '0106_pack_r_governance_decisions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to contract_records table."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Get existing columns
    cols = inspector.get_columns('contract_records')
    col_names = [c['name'] for c in cols]
    
    # Add missing columns if they don't exist
    if 'deal_id' not in col_names:
        op.add_column('contract_records', sa.Column('deal_id', sa.Integer(), nullable=False, server_default='0'))
    
    if 'professional_id' not in col_names:
        op.add_column('contract_records', sa.Column('professional_id', sa.Integer(), nullable=True))
    
    if 'status' not in col_names:
        op.add_column('contract_records', sa.Column('status', sa.String(50), nullable=False, server_default='draft'))
    
    if 'version' not in col_names:
        op.add_column('contract_records', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    
    if 'title' not in col_names:
        op.add_column('contract_records', sa.Column('title', sa.String(200), nullable=False, server_default='Untitled'))
    
    if 'updated_at' not in col_names:
        op.add_column('contract_records', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    
    if 'signed_at' not in col_names:
        op.add_column('contract_records', sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True))
    
    if 'storage_url' not in col_names:
        op.add_column('contract_records', sa.Column('storage_url', sa.String(500), nullable=True))
    
    # Drop old columns that don't match the schema
    if 'template_id' in col_names:
        op.drop_column('contract_records', 'template_id')
    
    if 'filename' in col_names:
        op.drop_column('contract_records', 'filename')
    
    if 'context_json' in col_names:
        op.drop_column('contract_records', 'context_json')


def downgrade() -> None:
    """Revert schema changes."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # This is a schema alteration, downgrade is not easily reversible
    # but we can at least document the original columns for reference
    pass
