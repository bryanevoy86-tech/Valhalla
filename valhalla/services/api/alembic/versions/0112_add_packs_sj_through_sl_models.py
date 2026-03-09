"""Add PACKS SJ, SK, SL models

Revision ID: 0112
Revises: 0111
Create Date: 2025-01-07 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0112'
down_revision = '0111'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK SJ: Wholesale Deal Machine
    op.create_table(
        'wholesale_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.String(255), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('seller_name', sa.String(255), nullable=True),
        sa.Column('seller_contact', sa.String(255), nullable=True),
        sa.Column('property_address', sa.String(500), nullable=True),
        sa.Column('motivation_level', sa.String(50), nullable=True),
        sa.Column('situation_notes', sa.Text(), nullable=True),
        sa.Column('stage', sa.String(50), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lead_id', name='uq_wholesale_leads_lead_id')
    )
    op.create_index('ix_wholesale_leads_stage', 'wholesale_leads', ['stage'])
    op.create_index('ix_wholesale_leads_source', 'wholesale_leads', ['source'])

    op.create_table(
        'wholesale_offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('offer_id', sa.String(255), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('offer_price', sa.Integer(), nullable=False),
        sa.Column('arv', sa.Integer(), nullable=True),
        sa.Column('repair_estimate', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['wholesale_leads.id'], ),
        sa.UniqueConstraint('offer_id', name='uq_wholesale_offers_offer_id')
    )
    op.create_index('ix_wholesale_offers_lead_id', 'wholesale_offers', ['lead_id'])
    op.create_index('ix_wholesale_offers_status', 'wholesale_offers', ['status'])

    op.create_table(
        'buyer_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact', sa.String(255), nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('buyer_id', name='uq_buyer_profiles_buyer_id')
    )
    op.create_index('ix_buyer_profiles_status', 'buyer_profiles', ['status'])

    op.create_table(
        'assignment_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.String(255), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('buyer_name', sa.String(255), nullable=True),
        sa.Column('buyer_contact', sa.String(255), nullable=True),
        sa.Column('assignment_fee', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['wholesale_leads.id'], ),
        sa.ForeignKeyConstraint(['buyer_id'], ['buyer_profiles.id'], ),
        sa.UniqueConstraint('assignment_id', name='uq_assignment_records_assignment_id')
    )
    op.create_index('ix_assignment_records_lead_id', 'assignment_records', ['lead_id'])
    op.create_index('ix_assignment_records_buyer_id', 'assignment_records', ['buyer_id'])
    op.create_index('ix_assignment_records_status', 'assignment_records', ['status'])

    op.create_table(
        'wholesale_pipeline_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.String(255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('total_leads', sa.Integer(), nullable=False),
        sa.Column('by_stage', sa.JSON(), nullable=True),
        sa.Column('hot_leads', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_offers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ready_for_assignment', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_id', name='uq_wholesale_pipeline_snapshots_snapshot_id')
    )
    op.create_index('ix_wholesale_pipeline_snapshots_date', 'wholesale_pipeline_snapshots', ['date'])

    # PACK SK: Arbitrage/Side-Hustle Opportunity Tracker
    op.create_table(
        'opportunities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('opportunity_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('startup_cost', sa.Integer(), nullable=False),
        sa.Column('expected_effort', sa.Float(), nullable=True),
        sa.Column('potential_return', sa.Integer(), nullable=True),
        sa.Column('risk_level', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='idea'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('opportunity_id', name='uq_opportunities_opportunity_id')
    )
    op.create_index('ix_opportunities_category', 'opportunities', ['category'])
    op.create_index('ix_opportunities_status', 'opportunities', ['status'])

    op.create_table(
        'opportunity_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('score_id', sa.String(255), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('time_efficiency', sa.Integer(), nullable=True),
        sa.Column('scalability', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('personal_interest', sa.Integer(), nullable=True),
        sa.Column('overall_score', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ),
        sa.UniqueConstraint('score_id', name='uq_opportunity_scores_score_id')
    )
    op.create_index('ix_opportunity_scores_opportunity_id', 'opportunity_scores', ['opportunity_id'])

    op.create_table(
        'opportunity_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(255), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('effort_hours', sa.Float(), nullable=True),
        sa.Column('revenue', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ),
        sa.UniqueConstraint('log_id', name='uq_opportunity_performance_log_id')
    )
    op.create_index('ix_opportunity_performance_opportunity_id', 'opportunity_performance', ['opportunity_id'])
    op.create_index('ix_opportunity_performance_date', 'opportunity_performance', ['date'])

    op.create_table(
        'opportunity_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('summary_id', sa.String(255), nullable=False),
        sa.Column('opportunity_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(10), nullable=False),
        sa.Column('total_effort_hours', sa.Float(), nullable=True),
        sa.Column('total_revenue', sa.Integer(), nullable=True),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('status_update', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ),
        sa.UniqueConstraint('summary_id', name='uq_opportunity_summaries_summary_id')
    )
    op.create_index('ix_opportunity_summaries_opportunity_id', 'opportunity_summaries', ['opportunity_id'])
    op.create_index('ix_opportunity_summaries_period', 'opportunity_summaries', ['period'])

    # PACK SL: Personal Master Dashboard
    op.create_table(
        'focus_areas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('area_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('priority_level', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('area_id', name='uq_focus_areas_area_id')
    )
    op.create_index('ix_focus_areas_category', 'focus_areas', ['category'])
    op.create_index('ix_focus_areas_priority_level', 'focus_areas', ['priority_level'])

    op.create_table(
        'personal_routines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('routine_id', sa.String(255), nullable=False),
        sa.Column('focus_area_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['focus_area_id'], ['focus_areas.id'], ),
        sa.UniqueConstraint('routine_id', name='uq_personal_routines_routine_id')
    )
    op.create_index('ix_personal_routines_focus_area_id', 'personal_routines', ['focus_area_id'])
    op.create_index('ix_personal_routines_frequency', 'personal_routines', ['frequency'])
    op.create_index('ix_personal_routines_status', 'personal_routines', ['status'])

    op.create_table(
        'routine_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('completion_id', sa.String(255), nullable=False),
        sa.Column('routine_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['routine_id'], ['personal_routines.id'], ),
        sa.UniqueConstraint('completion_id', name='uq_routine_completions_completion_id')
    )
    op.create_index('ix_routine_completions_routine_id', 'routine_completions', ['routine_id'])
    op.create_index('ix_routine_completions_date', 'routine_completions', ['date'])

    op.create_table(
        'family_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.String(255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('kids_notes', sa.JSON(), nullable=True),
        sa.Column('partner_notes', sa.Text(), nullable=True),
        sa.Column('home_operations', sa.Text(), nullable=True),
        sa.Column('highlights', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_id', name='uq_family_snapshots_snapshot_id')
    )
    op.create_index('ix_family_snapshots_date', 'family_snapshots', ['date'])

    op.create_table(
        'life_dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dashboard_id', sa.String(255), nullable=False),
        sa.Column('week_of', sa.DateTime(), nullable=False),
        sa.Column('wins', sa.JSON(), nullable=True),
        sa.Column('challenges', sa.JSON(), nullable=True),
        sa.Column('habits_tracked', sa.JSON(), nullable=True),
        sa.Column('upcoming_priorities', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dashboard_id', name='uq_life_dashboards_dashboard_id')
    )
    op.create_index('ix_life_dashboards_week_of', 'life_dashboards', ['week_of'])

    op.create_table(
        'personal_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('goal_id', name='uq_personal_goals_goal_id')
    )
    op.create_index('ix_personal_goals_category', 'personal_goals', ['category'])
    op.create_index('ix_personal_goals_status', 'personal_goals', ['status'])
    op.create_index('ix_personal_goals_deadline', 'personal_goals', ['deadline'])

    op.create_table(
        'mood_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.String(255), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('mood', sa.String(50), nullable=False),
        sa.Column('energy_level', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('log_id', name='uq_mood_logs_log_id')
    )
    op.create_index('ix_mood_logs_date', 'mood_logs', ['date'])
    op.create_index('ix_mood_logs_mood', 'mood_logs', ['mood'])


def downgrade() -> None:
    # Drop all PACKS SL tables
    op.drop_index('ix_mood_logs_mood', table_name='mood_logs')
    op.drop_index('ix_mood_logs_date', table_name='mood_logs')
    op.drop_table('mood_logs')

    op.drop_index('ix_personal_goals_deadline', table_name='personal_goals')
    op.drop_index('ix_personal_goals_status', table_name='personal_goals')
    op.drop_index('ix_personal_goals_category', table_name='personal_goals')
    op.drop_table('personal_goals')

    op.drop_index('ix_life_dashboards_week_of', table_name='life_dashboards')
    op.drop_table('life_dashboards')

    op.drop_index('ix_family_snapshots_date', table_name='family_snapshots')
    op.drop_table('family_snapshots')

    op.drop_index('ix_routine_completions_date', table_name='routine_completions')
    op.drop_index('ix_routine_completions_routine_id', table_name='routine_completions')
    op.drop_table('routine_completions')

    op.drop_index('ix_personal_routines_status', table_name='personal_routines')
    op.drop_index('ix_personal_routines_frequency', table_name='personal_routines')
    op.drop_index('ix_personal_routines_focus_area_id', table_name='personal_routines')
    op.drop_table('personal_routines')

    op.drop_index('ix_focus_areas_priority_level', table_name='focus_areas')
    op.drop_index('ix_focus_areas_category', table_name='focus_areas')
    op.drop_table('focus_areas')

    # Drop all PACKS SK tables
    op.drop_index('ix_opportunity_summaries_period', table_name='opportunity_summaries')
    op.drop_index('ix_opportunity_summaries_opportunity_id', table_name='opportunity_summaries')
    op.drop_table('opportunity_summaries')

    op.drop_index('ix_opportunity_performance_date', table_name='opportunity_performance')
    op.drop_index('ix_opportunity_performance_opportunity_id', table_name='opportunity_performance')
    op.drop_table('opportunity_performance')

    op.drop_index('ix_opportunity_scores_opportunity_id', table_name='opportunity_scores')
    op.drop_table('opportunity_scores')

    op.drop_index('ix_opportunities_status', table_name='opportunities')
    op.drop_index('ix_opportunities_category', table_name='opportunities')
    op.drop_table('opportunities')

    # Drop all PACKS SJ tables
    op.drop_index('ix_wholesale_pipeline_snapshots_date', table_name='wholesale_pipeline_snapshots')
    op.drop_table('wholesale_pipeline_snapshots')

    op.drop_index('ix_assignment_records_status', table_name='assignment_records')
    op.drop_index('ix_assignment_records_buyer_id', table_name='assignment_records')
    op.drop_index('ix_assignment_records_lead_id', table_name='assignment_records')
    op.drop_table('assignment_records')

    op.drop_index('ix_buyer_profiles_status', table_name='buyer_profiles')
    op.drop_table('buyer_profiles')

    op.drop_index('ix_wholesale_offers_status', table_name='wholesale_offers')
    op.drop_index('ix_wholesale_offers_lead_id', table_name='wholesale_offers')
    op.drop_table('wholesale_offers')

    op.drop_index('ix_wholesale_leads_source', table_name='wholesale_leads')
    op.drop_index('ix_wholesale_leads_stage', table_name='wholesale_leads')
    op.drop_table('wholesale_leads')
