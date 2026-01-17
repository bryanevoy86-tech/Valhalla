"""Add PACKS SA, SB, SC models

Revision ID: 0109
Revises: 0108
Create Date: 2025-01-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0109'
down_revision = '0108'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PACK SA: Grant Eligibility Engine
    op.create_table(
        'grant_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grant_id', sa.String(255), nullable=False),
        sa.Column('program_name', sa.String(255), nullable=False),
        sa.Column('funding_type', sa.String(100), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('target_groups', sa.JSON(), nullable=True),
        sa.Column('requirements', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grant_id', name='uq_grant_profiles_grant_id')
    )

    op.create_table(
        'eligibility_checklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grant_profile_id', sa.Integer(), nullable=False),
        sa.Column('requirement_id', sa.String(255), nullable=False),
        sa.Column('requirement_name', sa.String(255), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('uploaded_documents', sa.JSON(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['grant_profile_id'], ['grant_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_eligibility_checklists_grant_profile_id', 'eligibility_checklists', ['grant_profile_id'])

    # PACK SB: Business Registration Navigator
    op.create_table(
        'registration_flow_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=True),
        sa.Column('sequence_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('step_id', name='uq_registration_flow_steps_step_id')
    )

    op.create_table(
        'registration_stage_trackers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=True),
        sa.Column('business_description', sa.Text(), nullable=True),
        sa.Column('founders_list', sa.JSON(), nullable=True),
        sa.Column('stage_1_complete', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('selected_structure', sa.String(100), nullable=True),
        sa.Column('structure_details', sa.JSON(), nullable=True),
        sa.Column('stage_2_complete', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('documents_required', sa.JSON(), nullable=True),
        sa.Column('naics_codes', sa.JSON(), nullable=True),
        sa.Column('business_address', sa.String(255), nullable=True),
        sa.Column('stage_3_complete', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('filing_status', sa.String(50), nullable=False, server_default='not_filed'),
        sa.Column('filing_date', sa.DateTime(), nullable=True),
        sa.Column('stage_4_complete', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('registration_number', sa.String(100), nullable=True),
        sa.Column('articles_of_incorporation', sa.String(255), nullable=True),
        sa.Column('post_registration_notes', sa.Text(), nullable=True),
        sa.Column('stage_5_complete', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('overall_stage', sa.String(50), nullable=False, server_default='preparation'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # PACK SC: Banking & Accounts Structure Planner
    op.create_table(
        'bank_account_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('financial_institution', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='planned'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', name='uq_bank_account_plans_account_id')
    )
    op.create_index('ix_bank_account_plans_category', 'bank_account_plans', ['category'])

    op.create_table(
        'account_setup_checklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_plan_id', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default=False),
        sa.Column('required_documents', sa.JSON(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_plan_id'], ['bank_account_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_account_setup_checklists_account_plan_id', 'account_setup_checklists', ['account_plan_id'])

    op.create_table(
        'account_income_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_plan_id', sa.Integer(), nullable=False),
        sa.Column('income_source', sa.String(255), nullable=False),
        sa.Column('destination_account_id', sa.String(255), nullable=False),
        sa.Column('allocation_type', sa.String(50), nullable=False),
        sa.Column('allocation_value', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_plan_id'], ['bank_account_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_account_income_mappings_account_plan_id', 'account_income_mappings', ['account_plan_id'])


def downgrade() -> None:
    # PACK SC: Banking & Accounts Structure Planner
    op.drop_table('account_income_mappings')
    op.drop_table('account_setup_checklists')
    op.drop_table('bank_account_plans')

    # PACK SB: Business Registration Navigator
    op.drop_table('registration_stage_trackers')
    op.drop_table('registration_flow_steps')

    # PACK SA: Grant Eligibility Engine
    op.drop_table('eligibility_checklists')
    op.drop_table('grant_profiles')
