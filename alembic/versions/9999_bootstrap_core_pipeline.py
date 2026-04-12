"""Bootstrap core pipeline schema - clean initialization for Sprint 2.

This migration creates ONLY the core tables needed for the Lead -> Deal -> Offer -> Contract -> Buyer -> Dashboard pipeline.
It is designed to be run on a fresh database to initialize the schema without depending on historical migration chains.

Revision ID: 9999_bootstrap_core
Revises: None
Create Date: 2026-03-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9999_bootstrap_core'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = ['core_pipeline']
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core pipeline tables."""
    
    # Lead table
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
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
    
    # Deal table
    op.create_table(
        'deals',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
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
    
    # Offer table
    op.create_table(
        'offers',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deal_id', sa.Integer, sa.ForeignKey('deals.id'), nullable=False, index=True),
        sa.Column('offer_price', sa.Numeric(15, 2), nullable=False),
        sa.Column('emd_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('closing_window_days', sa.Integer, nullable=True),
        sa.Column('conditions_summary', sa.Text, nullable=True),
        sa.Column('generated_by', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='draft', index=True),
    )
    
    # Buyer table
    op.create_table(
        'buyers',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('buy_box_json', sa.JSON, nullable=True),
        sa.Column('preferred_markets', sa.String(255), nullable=True),
        sa.Column('cash_ready', sa.Boolean, default=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active', index=True),
    )
    
    # Contract table (already implemented, but ensure it exists)
    op.create_table(
        'contracts',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deal_id', sa.Integer, sa.ForeignKey('deals.id'), nullable=True, index=True),
        sa.Column('offer_id', sa.Integer, sa.ForeignKey('offers.id'), nullable=True, index=True),
        sa.Column('status', sa.String(50), nullable=False, default='draft', index=True),
        sa.Column('template_id', sa.String(255), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('pdf_url', sa.String(512), nullable=True),
        sa.Column('signing_status', sa.String(50), nullable=True),
        sa.Column('docusign_id', sa.String(255), nullable=True),
    )
    
    # Audit log table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('entity_id', sa.Integer, nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('previous_value', sa.JSON, nullable=True),
        sa.Column('new_value', sa.JSON, nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
    )
    
    # Buyer match log table
    op.create_table(
        'buyer_matches',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deal_id', sa.Integer, sa.ForeignKey('deals.id'), nullable=False, index=True),
        sa.Column('buyer_id', sa.Integer, sa.ForeignKey('buyers.id'), nullable=False, index=True),
        sa.Column('match_score', sa.Numeric(8, 2), nullable=True),
        sa.Column('match_reason', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
    )
    
    # Deal stage history for audit trail
    op.create_table(
        'deal_stage_history',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('deal_id', sa.Integer, sa.ForeignKey('deals.id'), nullable=False, index=True),
        sa.Column('old_stage', sa.String(50), nullable=True),
        sa.Column('new_stage', sa.String(50), nullable=False),
        sa.Column('override_reason', sa.Text, nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True),
    )


def downgrade() -> None:
    """Drop core pipeline tables."""
    op.drop_table('deal_stage_history')
    op.drop_table('buyer_matches')
    op.drop_table('audit_logs')
    op.drop_table('contracts')
    op.drop_table('buyers')
    op.drop_table('offers')
    op.drop_table('deals')
    op.drop_table('leads')

