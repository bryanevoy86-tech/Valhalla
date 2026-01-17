"""Add PACKS SG, SH, SI models

Revision ID: 0111
Revises: 0110
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0111'
down_revision = '0110'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK SG: Income Routing & Separation Engine
    op.create_table(
        'income_route_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.String(255), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('allocation_type', sa.String(50), nullable=False),
        sa.Column('allocation_value', sa.Float(), nullable=False),
        sa.Column('target_account', sa.String(255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_id', name='uq_income_route_rules_rule_id')
    )
    op.create_index('ix_income_route_rules_source', 'income_route_rules', ['source'])
    op.create_index('ix_income_route_rules_active', 'income_route_rules', ['active'])

    op.create_table(
        'income_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('routed', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('route_rule_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['route_rule_id'], ['income_route_rules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', name='uq_income_events_event_id')
    )
    op.create_index('ix_income_events_source', 'income_events', ['source'])
    op.create_index('ix_income_events_date', 'income_events', ['date'])
    op.create_index('ix_income_events_routed', 'income_events', ['routed'])

    op.create_table(
        'income_routing_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(255), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('income_event_id', sa.String(255), nullable=False),
        sa.Column('calculated_amount', sa.Integer(), nullable=False),
        sa.Column('target_account', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('user_approval_date', sa.DateTime(), nullable=True),
        sa.Column('execution_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['rule_id'], ['income_route_rules.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('log_id', name='uq_income_routing_logs_log_id')
    )
    op.create_index('ix_income_routing_logs_rule_id', 'income_routing_logs', ['rule_id'])
    op.create_index('ix_income_routing_logs_status', 'income_routing_logs', ['status'])

    op.create_table(
        'income_routing_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.String(255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_income', sa.Integer(), nullable=False),
        sa.Column('allocations', sa.JSON(), nullable=True),
        sa.Column('unallocated_balance', sa.Integer(), nullable=False, server_default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('summary_id', name='uq_income_routing_summaries_summary_id')
    )
    op.create_index('ix_income_routing_summaries_date', 'income_routing_summaries', ['date'])

    # PACK SH: Multi-Year Projection Snapshot Framework
    op.create_table(
        'projection_scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('assumptions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_id', name='uq_projection_scenarios_scenario_id')
    )

    op.create_table(
        'projection_years',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('expected_income', sa.Integer(), nullable=False),
        sa.Column('expected_expenses', sa.Integer(), nullable=False),
        sa.Column('expected_savings', sa.Integer(), nullable=False),
        sa.Column('expected_cashflow', sa.Integer(), nullable=False),
        sa.Column('expected_net_worth', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['scenario_id'], ['projection_scenarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scenario_id', 'year', name='uq_projection_years_scenario_year')
    )
    op.create_index('ix_projection_years_scenario_id', 'projection_years', ['scenario_id'])

    op.create_table(
        'projection_variances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('variance_id', sa.String(255), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(100), nullable=False),
        sa.Column('expected', sa.Integer(), nullable=False),
        sa.Column('actual', sa.Integer(), nullable=False),
        sa.Column('difference', sa.Integer(), nullable=False),
        sa.Column('difference_percent', sa.Float(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['scenario_id'], ['projection_scenarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('variance_id', name='uq_projection_variances_variance_id')
    )
    op.create_index('ix_projection_variances_scenario_id', 'projection_variances', ['scenario_id'])

    op.create_table(
        'projection_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.String(255), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.Column('narrative', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id', name='uq_projection_reports_report_id')
    )

    # PACK SI: Real Estate Acquisition & BRRRR Planner
    op.create_table(
        'brrrr_deals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('deal_id', sa.String(255), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('purchase_price', sa.Integer(), nullable=False),
        sa.Column('reno_budget', sa.Integer(), nullable=False),
        sa.Column('arv', sa.Integer(), nullable=True),
        sa.Column('strategy_notes', sa.Text(), nullable=True),
        sa.Column('acquisition_date', sa.DateTime(), nullable=True),
        sa.Column('reno_start_date', sa.DateTime(), nullable=True),
        sa.Column('reno_end_date', sa.DateTime(), nullable=True),
        sa.Column('refinance_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='analysis'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deal_id', name='uq_brrrr_deals_deal_id')
    )
    op.create_index('ix_brrrr_deals_status', 'brrrr_deals', ['status'])

    op.create_table(
        'brrrr_funding_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.String(255), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('down_payment', sa.Integer(), nullable=False),
        sa.Column('renovation_funds_source', sa.String(255), nullable=True),
        sa.Column('holding_costs_plan', sa.String(255), nullable=True),
        sa.Column('refinance_strategy', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['deal_id'], ['brrrr_deals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', name='uq_brrrr_funding_plans_plan_id')
    )
    op.create_index('ix_brrrr_funding_plans_deal_id', 'brrrr_funding_plans', ['deal_id'])

    op.create_table(
        'brrrr_cashflow_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entry_id', sa.String(255), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('rent', sa.Integer(), nullable=False),
        sa.Column('expenses', sa.Integer(), nullable=False),
        sa.Column('net', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['deal_id'], ['brrrr_deals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_id', name='uq_brrrr_cashflow_entries_entry_id')
    )
    op.create_index('ix_brrrr_cashflow_entries_deal_id', 'brrrr_cashflow_entries', ['deal_id'])
    op.create_index('ix_brrrr_cashflow_entries_date', 'brrrr_cashflow_entries', ['date'])

    op.create_table(
        'brrrr_refinance_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.String(255), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('new_loan_amount', sa.Integer(), nullable=False),
        sa.Column('interest_rate', sa.Float(), nullable=False),
        sa.Column('loan_term_months', sa.Integer(), nullable=True),
        sa.Column('cash_out_amount', sa.Integer(), nullable=False),
        sa.Column('new_payment', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['deal_id'], ['brrrr_deals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_id', name='uq_brrrr_refinance_snapshots_snapshot_id')
    )
    op.create_index('ix_brrrr_refinance_snapshots_deal_id', 'brrrr_refinance_snapshots', ['deal_id'])

    op.create_table(
        'brrrr_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.String(255), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=False),
        sa.Column('purchase_price', sa.Integer(), nullable=False),
        sa.Column('reno_actual', sa.Integer(), nullable=True),
        sa.Column('reno_budget', sa.Integer(), nullable=True),
        sa.Column('arv', sa.Integer(), nullable=True),
        sa.Column('initial_equity', sa.Integer(), nullable=True),
        sa.Column('refi_loan_amount', sa.Integer(), nullable=True),
        sa.Column('cash_out', sa.Integer(), nullable=True),
        sa.Column('current_monthly_cashflow', sa.Integer(), nullable=True),
        sa.Column('annualized_cashflow', sa.Integer(), nullable=True),
        sa.Column('timeline', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('summary_id', name='uq_brrrr_summaries_summary_id')
    )


def downgrade() -> None:
    # PACK SI: Real Estate Acquisition & BRRRR Planner
    op.drop_table('brrrr_summaries')
    op.drop_table('brrrr_refinance_snapshots')
    op.drop_table('brrrr_cashflow_entries')
    op.drop_table('brrrr_funding_plans')
    op.drop_table('brrrr_deals')

    # PACK SH: Multi-Year Projection Snapshot Framework
    op.drop_table('projection_reports')
    op.drop_table('projection_variances')
    op.drop_table('projection_years')
    op.drop_table('projection_scenarios')

    # PACK SG: Income Routing & Separation Engine
    op.drop_table('income_routing_summaries')
    op.drop_table('income_routing_logs')
    op.drop_table('income_events')
    op.drop_table('income_route_rules')
