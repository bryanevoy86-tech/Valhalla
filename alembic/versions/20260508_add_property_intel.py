"""Add heimdall property intel table

Revision ID: 20260508_add_property_intel
Revises: 650836770c62
Create Date: 2026-05-08 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '20260508_add_property_intel'
down_revision = '650836770c62'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Create heimdall_property_intel table if it doesn't exist
    if "heimdall_property_intel" not in inspector.get_table_names():
        op.create_table(
            'heimdall_property_intel',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('address', sa.String(), nullable=False),
            sa.Column('city', sa.String(), nullable=False),
            sa.Column('province_or_state', sa.String(), nullable=True),
            sa.Column('country', sa.String(), nullable=True),
            sa.Column('research_status', sa.String(), nullable=False, server_default='NEW'),
            sa.Column('distress_score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('lead_lane', sa.String(), nullable=False, server_default='UNSCORED'),
            sa.Column('ownership_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('outreach_allowed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('converted_to_lead', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('raw_address_payload', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('property_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('research_plan', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('distress_analysis', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('notes', sa.JSON(), nullable=False, server_default='[]'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_heimdall_property_intel_address', 'heimdall_property_intel', ['address'])
        op.create_index('ix_heimdall_property_intel_city', 'heimdall_property_intel', ['city'])
        op.create_index('ix_heimdall_property_intel_province_or_state', 'heimdall_property_intel', ['province_or_state'])
        op.create_index('ix_heimdall_property_intel_country', 'heimdall_property_intel', ['country'])
        op.create_index('ix_heimdall_property_intel_research_status', 'heimdall_property_intel', ['research_status'])
        op.create_index('ix_heimdall_property_intel_distress_score', 'heimdall_property_intel', ['distress_score'])
        op.create_index('ix_heimdall_property_intel_lead_lane', 'heimdall_property_intel', ['lead_lane'])


def downgrade() -> None:
    op.drop_table('heimdall_property_intel')
