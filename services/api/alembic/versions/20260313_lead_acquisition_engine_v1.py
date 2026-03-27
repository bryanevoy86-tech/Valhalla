"""Lead acquisition engine - source registry and ingestion tables.

Revision ID: 20260313_lead_acquisition_engine_v1
Revises: 0065
Create Date: 2026-03-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260313_lead_acquisition_engine_v1'
down_revision = '0065'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lead_sources table
    op.create_table(
        'lead_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('sector', sa.String(100), nullable=True),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('scrape_frequency', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('auth_type', sa.String(50), nullable=False, server_default='none'),
        sa.Column('parser_type', sa.String(50), nullable=False, server_default='json'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_success_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='inactive'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_sources_active'), 'lead_sources', ['active'], unique=False)
    op.create_index(op.f('ix_lead_sources_name'), 'lead_sources', ['name'], unique=False)
    
    # Create raw_leads table
    op.create_table(
        'raw_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('raw_hash', sa.String(64), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=False),
        sa.Column('imported_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['lead_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_leads_imported_at'), 'raw_leads', ['imported_at'], unique=False)
    op.create_index(op.f('ix_raw_leads_raw_hash'), 'raw_leads', ['raw_hash'], unique=False)
    op.create_index(op.f('ix_raw_leads_source_id'), 'raw_leads', ['source_id'], unique=False)
    
    # Create normalized_leads table
    op.create_table(
        'normalized_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('market', sa.String(100), nullable=True),
        sa.Column('lead_type', sa.String(50), nullable=True),
        sa.Column('asking_price', sa.Float(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('duplicate_of', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['lead_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_normalized_leads_city'), 'normalized_leads', ['city'], unique=False)
    op.create_index(op.f('ix_normalized_leads_company_name'), 'normalized_leads', ['company_name'], unique=False)
    op.create_index(op.f('ix_normalized_leads_created_at'), 'normalized_leads', ['created_at'], unique=False)
    op.create_index(op.f('ix_normalized_leads_email'), 'normalized_leads', ['email'], unique=False)
    op.create_index(op.f('ix_normalized_leads_external_id'), 'normalized_leads', ['external_id'], unique=False)
    op.create_index(op.f('ix_normalized_leads_market'), 'normalized_leads', ['market'], unique=False)
    op.create_index(op.f('ix_normalized_leads_phone'), 'normalized_leads', ['phone'], unique=False)
    op.create_index(op.f('ix_normalized_leads_source_id'), 'normalized_leads', ['source_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_normalized_leads_source_id'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_phone'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_market'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_external_id'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_email'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_created_at'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_company_name'), table_name='normalized_leads')
    op.drop_index(op.f('ix_normalized_leads_city'), table_name='normalized_leads')
    op.drop_table('normalized_leads')
    op.drop_index(op.f('ix_raw_leads_source_id'), table_name='raw_leads')
    op.drop_index(op.f('ix_raw_leads_raw_hash'), table_name='raw_leads')
    op.drop_index(op.f('ix_raw_leads_imported_at'), table_name='raw_leads')
    op.drop_table('raw_leads')
    op.drop_index(op.f('ix_lead_sources_name'), table_name='lead_sources')
    op.drop_index(op.f('ix_lead_sources_active'), table_name='lead_sources')
    op.drop_table('lead_sources')
