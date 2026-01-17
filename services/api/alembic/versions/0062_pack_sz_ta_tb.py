"""
Alembic migration for PACK SZ, TA, TB

PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive
PACK TA: Trust, Loyalty & Relationship Mapping  
PACK TB: Daily Behavioral Rhythm & Tempo Engine

Revision ID: 0062_pack_sz_ta_tb
Revises: 0061_pack_sw_sx_sy
Create Date: 2024-12-19 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import logging

logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "0062_pack_sz_ta_tb"
down_revision = "0061_pack_sw_sx_sy"
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration: Create PACK SZ, TA, TB tables."""

    # --- PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive ---

    # Create philosophy_records table
    try:
        op.create_table(
            'philosophy_records',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('record_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('pillars', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('mission_statement', sa.Text(), nullable=False),
            sa.Column('values', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('rules_to_follow', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('rules_to_never_break', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('long_term_intent', sa.Text(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        logger.info("[migration 0062] philosophy_records table created")
    except Exception as e:
        logger.warning(f"[migration 0062] philosophy_records already exists or error: {e}")

    # Create empire_principles table
    try:
        op.create_table(
            'empire_principles',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('principle_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('record_id', sa.Integer(), sa.ForeignKey('philosophy_records.id', ondelete='CASCADE'), nullable=False),
            sa.Column('category', sa.String(50), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('enforcement_level', sa.String(20), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index('idx_empire_principles_record_id', 'empire_principles', ['record_id'])
        op.create_index('idx_empire_principles_category', 'empire_principles', ['category'])
        logger.info("[migration 0062] empire_principles table created")
    except Exception as e:
        logger.warning(f"[migration 0062] empire_principles already exists or error: {e}")

    # Create philosophy_snapshots table
    try:
        op.create_table(
            'philosophy_snapshots',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('snapshot_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('core_pillars', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('recent_updates', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('impact_on_system', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('user_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        logger.info("[migration 0062] philosophy_snapshots table created")
    except Exception as e:
        logger.warning(f"[migration 0062] philosophy_snapshots already exists or error: {e}")

    # --- PACK TA: Trust, Loyalty & Relationship Mapping ---

    # Create relationship_profiles table
    try:
        op.create_table(
            'relationship_profiles',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('profile_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('role', sa.String(100), nullable=False),
            sa.Column('relationship_type', sa.String(50), nullable=False),
            sa.Column('user_defined_trust_level', sa.Integer(), nullable=False),
            sa.Column('boundaries', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index('idx_relationship_profiles_role', 'relationship_profiles', ['role'])
        logger.info("[migration 0062] relationship_profiles table created")
    except Exception as e:
        logger.warning(f"[migration 0062] relationship_profiles already exists or error: {e}")

    # Create trust_event_logs table
    try:
        op.create_table(
            'trust_event_logs',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('event_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('profile_id', sa.Integer(), sa.ForeignKey('relationship_profiles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('event_description', sa.Text(), nullable=False),
            sa.Column('trust_change', sa.Integer(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index('idx_trust_event_logs_profile_id', 'trust_event_logs', ['profile_id'])
        logger.info("[migration 0062] trust_event_logs table created")
    except Exception as e:
        logger.warning(f"[migration 0062] trust_event_logs already exists or error: {e}")

    # Create relationship_map_snapshots table
    try:
        op.create_table(
            'relationship_map_snapshots',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('snapshot_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('key_people', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('trust_levels', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.Column('boundaries', postgresql.JSON(), nullable=False, server_default='{}'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        logger.info("[migration 0062] relationship_map_snapshots table created")
    except Exception as e:
        logger.warning(f"[migration 0062] relationship_map_snapshots already exists or error: {e}")

    # --- PACK TB: Daily Behavioral Rhythm & Tempo Engine ---

    # Create daily_rhythm_profiles table
    try:
        op.create_table(
            'daily_rhythm_profiles',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('profile_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('wake_time', sa.String(5), nullable=False),
            sa.Column('sleep_time', sa.String(5), nullable=False),
            sa.Column('peak_focus_blocks', postgresql.JSON(), nullable=False, server_default='[]'),
            sa.Column('low_energy_blocks', postgresql.JSON(), nullable=False, server_default='[]'),
            sa.Column('family_blocks', postgresql.JSON(), nullable=False, server_default='[]'),
            sa.Column('personal_time_blocks', postgresql.JSON(), nullable=False, server_default='[]'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        logger.info("[migration 0062] daily_rhythm_profiles table created")
    except Exception as e:
        logger.warning(f"[migration 0062] daily_rhythm_profiles already exists or error: {e}")

    # Create tempo_rules table
    try:
        op.create_table(
            'tempo_rules',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('rule_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('profile_id', sa.Integer(), sa.ForeignKey('daily_rhythm_profiles.id', ondelete='CASCADE'), nullable=False),
            sa.Column('time_block', sa.String(50), nullable=False),
            sa.Column('action_intensity', sa.String(20), nullable=False),
            sa.Column('communication_style', sa.String(20), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        op.create_index('idx_tempo_rules_profile_id', 'tempo_rules', ['profile_id'])
        logger.info("[migration 0062] tempo_rules table created")
    except Exception as e:
        logger.warning(f"[migration 0062] tempo_rules already exists or error: {e}")

    # Create daily_tempo_snapshots table
    try:
        op.create_table(
            'daily_tempo_snapshots',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('snapshot_id', sa.String(50), unique=True, nullable=False, index=True),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('rhythm_followed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('adjustments_needed', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
            sa.Column('user_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        )
        logger.info("[migration 0062] daily_tempo_snapshots table created")
    except Exception as e:
        logger.warning(f"[migration 0062] daily_tempo_snapshots already exists or error: {e}")

    logger.info("[migration 0062] PACK SZ, TA, TB migration completed successfully")


def downgrade():
    """Rollback migration: Drop PACK SZ, TA, TB tables."""

    # Drop in reverse order of creation
    try:
        op.drop_table('daily_tempo_snapshots')
        logger.info("[migration 0062] daily_tempo_snapshots table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] daily_tempo_snapshots drop failed: {e}")

    try:
        op.drop_table('tempo_rules')
        logger.info("[migration 0062] tempo_rules table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] tempo_rules drop failed: {e}")

    try:
        op.drop_table('daily_rhythm_profiles')
        logger.info("[migration 0062] daily_rhythm_profiles table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] daily_rhythm_profiles drop failed: {e}")

    try:
        op.drop_table('relationship_map_snapshots')
        logger.info("[migration 0062] relationship_map_snapshots table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] relationship_map_snapshots drop failed: {e}")

    try:
        op.drop_table('trust_event_logs')
        logger.info("[migration 0062] trust_event_logs table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] trust_event_logs drop failed: {e}")

    try:
        op.drop_table('relationship_profiles')
        logger.info("[migration 0062] relationship_profiles table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] relationship_profiles drop failed: {e}")

    try:
        op.drop_table('philosophy_snapshots')
        logger.info("[migration 0062] philosophy_snapshots table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] philosophy_snapshots drop failed: {e}")

    try:
        op.drop_table('empire_principles')
        logger.info("[migration 0062] empire_principles table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] empire_principles drop failed: {e}")

    try:
        op.drop_table('philosophy_records')
        logger.info("[migration 0062] philosophy_records table dropped")
    except Exception as e:
        logger.warning(f"[migration 0062] philosophy_records drop failed: {e}")

    logger.info("[migration 0062] PACK SZ, TA, TB rollback completed")
