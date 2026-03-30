"""create_core_pipeline_tables

Revision ID: f2b00b1c2d4c
Revises: f2af0b1c2d4b
Create Date: 2026-03-05 00:00:00.000000

Frontend phase 1 blocker fix: Ensure leads and deals tables exist for GET /api/deals endpoint.
This migration creates the core pipeline tables needed for the lead->deal->offer flow.
Uses IF NOT EXISTS to handle cases where tables may already exist.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2b00b1c2d4c'
down_revision: Union[str, Sequence[str], None] = 'f2af0b1c2d4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core pipeline tables for leads and deals."""
    
    # Get the current bind and database type
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Create leads table using raw SQL with IF NOT EXISTS
    if dialect_name == 'postgresql':
        op.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                source VARCHAR(255),
                lead_name VARCHAR(255),
                lead_email VARCHAR(255),
                lead_phone VARCHAR(20),
                property_address VARCHAR(512),
                property_city VARCHAR(255),
                property_state VARCHAR(2),
                property_zip VARCHAR(10),
                estimated_arv NUMERIC(15, 2),
                lead_status VARCHAR(50) DEFAULT 'new' NOT NULL,
                notes TEXT
            )
        """)
        
        # Create indices
        op.execute("CREATE INDEX IF NOT EXISTS ix_leads_source ON leads (source)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_leads_state ON leads (property_state)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (lead_status)")
        
        # Create deals table using raw SQL with IF NOT EXISTS  
        op.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                lead_id INTEGER NOT NULL REFERENCES leads(id),
                title VARCHAR(255) NOT NULL,
                stage VARCHAR(50) DEFAULT 'lead_received' NOT NULL,
                status VARCHAR(50) DEFAULT 'active' NOT NULL,
                arv NUMERIC(15, 2),
                estimated_repair_cost NUMERIC(15, 2),
                max_allowable_offer NUMERIC(15, 2),
                target_assignment_fee NUMERIC(15, 2),
                score NUMERIC(8, 2) DEFAULT 0,
                notes TEXT,
                disposition_status VARCHAR(50)
            )
        """)
        
        # Create indices
        op.execute("CREATE INDEX IF NOT EXISTS ix_deals_lead_id ON deals (lead_id)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_deals_stage ON deals (stage)")
        op.execute("CREATE INDEX IF NOT EXISTS ix_deals_status ON deals (status)")
        
    else:
        # SQLite fallback
        op.create_table(
            'leads',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('source', sa.String(255), nullable=True, index=True),
            sa.Column('lead_name', sa.String(255), nullable=True),
            sa.Column('lead_email', sa.String(255), nullable=True),
            sa.Column('lead_phone', sa.String(20), nullable=True),
            sa.Column('property_address', sa.String(512), nullable=True),
            sa.Column('property_city', sa.String(255), nullable=True),
            sa.Column('property_state', sa.String(2), nullable=True, index=True),
            sa.Column('property_zip', sa.String(10), nullable=True),
            sa.Column('estimated_arv', sa.Numeric(15, 2), nullable=True),
            sa.Column('lead_status', sa.String(50), nullable=False, default='new', index=True),
            sa.Column('notes', sa.Text, nullable=True),
        )
        
        op.create_table(
            'deals',
            sa.Column('id', sa.Integer, primary_key=True, index=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('lead_id', sa.Integer, sa.ForeignKey('leads.id'), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('stage', sa.String(50), nullable=False, default='lead_received', index=True),
            sa.Column('status', sa.String(50), nullable=False, default='active', index=True),
            sa.Column('arv', sa.Numeric(15, 2), nullable=True),
            sa.Column('estimated_repair_cost', sa.Numeric(15, 2), nullable=True),
            sa.Column('max_allowable_offer', sa.Numeric(15, 2), nullable=True),
            sa.Column('target_assignment_fee', sa.Numeric(15, 2), nullable=True),
            sa.Column('score', sa.Numeric(8, 2), nullable=True, default=0),
            sa.Column('notes', sa.Text, nullable=True),
            sa.Column('disposition_status', sa.String(50), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema - drop tables if they exist."""
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    if dialect_name == 'postgresql':
        op.execute("DROP TABLE IF EXISTS deals CASCADE")
        op.execute("DROP TABLE IF EXISTS leads CASCADE")
    else:
        op.drop_table('deals', if_exists=True)
        op.drop_table('leads', if_exists=True)
