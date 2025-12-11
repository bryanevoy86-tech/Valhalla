"""Add PACKS SD, SE, SF models

Revision ID: 0110
Revises: 0109
Create Date: 2025-01-07 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0110'
down_revision = '0109'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK SD: Credit Card & Spending Framework
    op.create_table(
        'credit_card_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('card_id', sa.String(255), nullable=False),
        sa.Column('nickname', sa.String(255), nullable=True),
        sa.Column('issuer', sa.String(255), nullable=True),
        sa.Column('card_type', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('allowed_categories', sa.JSON(), nullable=True),
        sa.Column('restricted_categories', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('card_id', name='uq_credit_card_profiles_card_id')
    )
    op.create_index('ix_credit_card_profiles_status', 'credit_card_profiles', ['status'])

    op.create_table(
        'spending_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.String(255), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('business_allowed', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('personal_allowed', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['card_id'], ['credit_card_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_id', name='uq_spending_rules_rule_id')
    )
    op.create_index('ix_spending_rules_card_id', 'spending_rules', ['card_id'])

    op.create_table(
        'spending_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(255), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('merchant', sa.String(255), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('detected_category', sa.String(100), nullable=True),
        sa.Column('user_classification', sa.String(100), nullable=True),
        sa.Column('rule_compliant', sa.Boolean(), nullable=False, server_default=True),
        sa.Column('flagged', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('flag_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['card_id'], ['credit_card_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id', name='uq_spending_transactions_transaction_id')
    )
    op.create_index('ix_spending_transactions_card_id', 'spending_transactions', ['card_id'])
    op.create_index('ix_spending_transactions_date', 'spending_transactions', ['date'])
    op.create_index('ix_spending_transactions_flagged', 'spending_transactions', ['flagged'])

    op.create_table(
        'monthly_spending_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('total_business', sa.Integer(), nullable=False, server_default=0),
        sa.Column('total_personal', sa.Integer(), nullable=False, server_default=0),
        sa.Column('total_flagged', sa.Integer(), nullable=False, server_default=0),
        sa.Column('flagged_transactions', sa.JSON(), nullable=True),
        sa.Column('category_breakdown', sa.JSON(), nullable=True),
        sa.Column('unusual_items', sa.JSON(), nullable=True),
        sa.Column('subscription_list', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['card_id'], ['credit_card_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('card_id', 'year', 'month', name='uq_monthly_spending_summaries_card_year_month')
    )
    op.create_index('ix_monthly_spending_summaries_card_id', 'monthly_spending_summaries', ['card_id'])

    # PACK SE: Vehicle Use & Expense Categorization
    op.create_table(
        'vehicle_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(100), nullable=True),
        sa.Column('ownership', sa.String(100), nullable=True),
        sa.Column('make', sa.String(100), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('vin', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vehicle_id', name='uq_vehicle_profiles_vehicle_id')
    )
    op.create_index('ix_vehicle_profiles_status', 'vehicle_profiles', ['status'])

    op.create_table(
        'vehicle_trip_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trip_id', sa.String(255), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('start_location', sa.String(255), nullable=True),
        sa.Column('end_location', sa.String(255), nullable=True),
        sa.Column('kms', sa.Float(), nullable=False),
        sa.Column('purpose', sa.String(255), nullable=True),
        sa.Column('business_use', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('personal_use', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('mixed_use', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('business_kms', sa.Float(), nullable=False, server_default=0),
        sa.Column('personal_kms', sa.Float(), nullable=False, server_default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicle_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', name='uq_vehicle_trip_logs_trip_id')
    )
    op.create_index('ix_vehicle_trip_logs_vehicle_id', 'vehicle_trip_logs', ['vehicle_id'])
    op.create_index('ix_vehicle_trip_logs_date', 'vehicle_trip_logs', ['date'])

    op.create_table(
        'vehicle_expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.String(255), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('business_related', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('business_percentage', sa.Float(), nullable=False, server_default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('receipt_url', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicle_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('expense_id', name='uq_vehicle_expenses_expense_id')
    )
    op.create_index('ix_vehicle_expenses_vehicle_id', 'vehicle_expenses', ['vehicle_id'])
    op.create_index('ix_vehicle_expenses_category', 'vehicle_expenses', ['category'])

    op.create_table(
        'mileage_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('total_kms', sa.Float(), nullable=False),
        sa.Column('business_kms', sa.Float(), nullable=False),
        sa.Column('personal_kms', sa.Float(), nullable=False),
        sa.Column('mixed_kms', sa.Float(), nullable=False),
        sa.Column('business_percentage', sa.Float(), nullable=False),
        sa.Column('trip_count', sa.Integer(), nullable=False),
        sa.Column('repetitive_routes', sa.JSON(), nullable=True),
        sa.Column('unusual_days', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicle_profiles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vehicle_id', 'period', name='uq_mileage_summaries_vehicle_period')
    )
    op.create_index('ix_mileage_summaries_vehicle_id', 'mileage_summaries', ['vehicle_id'])

    # PACK SF: CRA Document Vault & Organization
    op.create_table(
        'cra_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(255), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=True),
        sa.Column('transaction_id', sa.String(255), nullable=True),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('flagged', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('flag_reason', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_id', name='uq_cra_documents_doc_id')
    )
    op.create_index('ix_cra_documents_year', 'cra_documents', ['year'])
    op.create_index('ix_cra_documents_category', 'cra_documents', ['category'])
    op.create_index('ix_cra_documents_flagged', 'cra_documents', ['flagged'])

    op.create_table(
        'cra_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_income', sa.Integer(), nullable=False, server_default=0),
        sa.Column('total_business_expenses', sa.Integer(), nullable=False, server_default=0),
        sa.Column('total_personal_expenses', sa.Integer(), nullable=False, server_default=0),
        sa.Column('income_breakdown', sa.JSON(), nullable=True),
        sa.Column('expense_breakdown', sa.JSON(), nullable=True),
        sa.Column('vehicle_expenses', sa.Integer(), nullable=False, server_default=0),
        sa.Column('vehicle_kms', sa.Float(), nullable=False, server_default=0),
        sa.Column('flagged_items', sa.JSON(), nullable=True),
        sa.Column('unusual_transactions', sa.JSON(), nullable=True),
        sa.Column('documentation_gaps', sa.JSON(), nullable=True),
        sa.Column('questions_for_accountant', sa.JSON(), nullable=True),
        sa.Column('supporting_documents', sa.JSON(), nullable=True),
        sa.Column('review_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('accountant_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('summary_id', name='uq_cra_summaries_summary_id'),
        sa.UniqueConstraint('year', name='uq_cra_summaries_year')
    )
    op.create_index('ix_cra_summaries_year', 'cra_summaries', ['year'])
    op.create_index('ix_cra_summaries_review_status', 'cra_summaries', ['review_status'])

    op.create_table(
        'cra_category_maps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('user_defined_description', sa.Text(), nullable=True),
        sa.Column('cra_line_reference', sa.String(100), nullable=True),
        sa.Column('example_transactions', sa.JSON(), nullable=True),
        sa.Column('typical_business_use', sa.Text(), nullable=True),
        sa.Column('typical_personal_use', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', name='uq_cra_category_maps_category_id')
    )

    op.create_table(
        'fiscal_year_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.String(255), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('fiscal_year_end', sa.String(20), nullable=True),
        sa.Column('transaction_count', sa.Integer(), nullable=False, server_default=0),
        sa.Column('total_amount', sa.Integer(), nullable=False, server_default=0),
        sa.Column('documents_count', sa.Integer(), nullable=False, server_default=0),
        sa.Column('documents_by_category', sa.JSON(), nullable=True),
        sa.Column('flagged_count', sa.Integer(), nullable=False, server_default=0),
        sa.Column('flagged_summary', sa.JSON(), nullable=True),
        sa.Column('recurring_count', sa.Integer(), nullable=False, server_default=0),
        sa.Column('recurring_list', sa.JSON(), nullable=True),
        sa.Column('vehicle_count', sa.Integer(), nullable=False, server_default=0),
        sa.Column('total_vehicle_kms', sa.Float(), nullable=False, server_default=0),
        sa.Column('business_vehicle_percentage', sa.Float(), nullable=False, server_default=0),
        sa.Column('gaps_identified', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('gap_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_id', name='uq_fiscal_year_snapshots_snapshot_id')
    )
    op.create_index('ix_fiscal_year_snapshots_year', 'fiscal_year_snapshots', ['year'])


def downgrade() -> None:
    # PACK SF: CRA Document Vault & Organization
    op.drop_table('fiscal_year_snapshots')
    op.drop_table('cra_category_maps')
    op.drop_table('cra_summaries')
    op.drop_table('cra_documents')

    # PACK SE: Vehicle Use & Expense Categorization
    op.drop_table('mileage_summaries')
    op.drop_table('vehicle_expenses')
    op.drop_table('vehicle_trip_logs')
    op.drop_table('vehicle_profiles')

    # PACK SD: Credit Card & Spending Framework
    op.drop_table('monthly_spending_summaries')
    op.drop_table('spending_transactions')
    op.drop_table('spending_rules')
    op.drop_table('credit_card_profiles')
