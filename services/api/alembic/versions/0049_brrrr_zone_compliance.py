"""Pack 49: Global BRRRR Zone Compliance Profiles

Revision ID: 0049_brrrr_zone_compliance
Revises: 0048_heimdall_behavior_core
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0049_brrrr_zone_compliance'
down_revision = '0048_heimdall_behavior_core'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # jurisdictions: legal zones (countries/states/territories)
    op.create_table(
        'jurisdictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_code', sa.String(16), nullable=False),
        sa.Column('zone_name', sa.String(128), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('region', sa.String(64), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('zone_code', name='uq_jurisdictions_zone_code')
    )

    # compliance_rules: per-zone legal requirements
    op.create_table(
        'compliance_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_code', sa.String(16), nullable=False),
        sa.Column('rule_key', sa.String(64), nullable=False),
        sa.Column('rule_value', sa.Text(), nullable=False),
        sa.Column('applies_to_deal_types', sa.Text(), nullable=True),  # JSON array
        sa.Column('severity', sa.String(16), server_default='warning', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_compliance_rules_zone_code', 'compliance_rules', ['zone_code'])

    # required_documents: per-zone paperwork checklists
    op.create_table(
        'required_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_code', sa.String(16), nullable=False),
        sa.Column('deal_type', sa.String(32), nullable=False),
        sa.Column('doc_name', sa.String(128), nullable=False),
        sa.Column('doc_category', sa.String(64), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_required_documents_zone_deal', 'required_documents', ['zone_code', 'deal_type'])

    # tax_bands: graduated tax rates by property value
    op.create_table(
        'tax_bands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_code', sa.String(16), nullable=False),
        sa.Column('tax_type', sa.String(32), nullable=False),
        sa.Column('min_value', sa.Numeric(14, 2), nullable=False),
        sa.Column('max_value', sa.Numeric(14, 2), nullable=True),
        sa.Column('rate_pct', sa.Numeric(7, 4), nullable=False),
        sa.Column('flat_fee', sa.Numeric(10, 2), server_default=sa.text("0"), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tax_bands_zone_type', 'tax_bands', ['zone_code', 'tax_type'])

    # compliance_events: audit trail of zone evaluations
    op.create_table(
        'compliance_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_code', sa.String(16), nullable=False),
        sa.Column('deal_type', sa.String(32), nullable=False),
        sa.Column('result', sa.String(16), nullable=False),
        sa.Column('warnings', sa.Text(), nullable=True),  # JSON array
        sa.Column('risk_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('snapshot_json', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_compliance_events_zone', 'compliance_events', ['zone_code'])

    # risk_flags: red flags for foreign ownership, entity type, etc.
    op.create_table(
        'risk_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_code', sa.String(16), nullable=False),
        sa.Column('flag_name', sa.String(64), nullable=False),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('risk_impact', sa.String(16), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_risk_flags_zone', 'risk_flags', ['zone_code'])


def downgrade() -> None:
    op.drop_index('ix_risk_flags_zone', table_name='risk_flags')
    op.drop_table('risk_flags')
    op.drop_index('ix_compliance_events_zone', table_name='compliance_events')
    op.drop_table('compliance_events')
    op.drop_index('ix_tax_bands_zone_type', table_name='tax_bands')
    op.drop_table('tax_bands')
    op.drop_index('ix_required_documents_zone_deal', table_name='required_documents')
    op.drop_table('required_documents')
    op.drop_index('ix_compliance_rules_zone_code', table_name='compliance_rules')
    op.drop_table('compliance_rules')
    op.drop_table('jurisdictions')
