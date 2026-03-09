"""
Alembic migration: Add Heimdall Ultra Mode configuration table

Revision ID: 0063_heimdall_ultra_mode
Revises: 0062_pack_sz_ta_tb
Create Date: 2024-12-20 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import logging

logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision = "0063_heimdall_ultra_mode"
down_revision = "0062_pack_sz_ta_tb"
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration: Create heimdall_ultra_config table."""

    try:
        op.create_table(
            'heimdall_ultra_config',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('initiative_level', sa.String(), nullable=False, server_default="'maximum'"),
            sa.Column('auto_prepare_tasks', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('auto_generate_next_steps', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('auto_close_loops', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('escalation_chain', postgresql.JSON(), nullable=False, server_default=sa.text("'{\"operations\": \"ODIN\", \"risk\": \"TYR\", \"creativity\": \"LOKI\", \"family\": \"QUEEN\", \"default\": \"KING\"}'::json")),
            sa.Column('priority_matrix', postgresql.JSON(), nullable=False, server_default=sa.text("'[\"family_stability\", \"financial_safety\", \"empire_growth\", \"operational_velocity\", \"energy_conservation\", \"mental_load_reduction\"]'::json")),
            sa.Column('scan_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('scan_frequency_minutes', sa.Integer(), nullable=False, server_default='60'),
            sa.Column('track_all_user_inputs', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('tempo_profile', sa.String(), nullable=False, server_default="'default'"),
        )
        logger.info("[migration 0063] heimdall_ultra_config table created")
    except Exception as e:
        logger.warning(f"[migration 0063] heimdall_ultra_config already exists or error: {e}")


def downgrade():
    """Rollback migration: Drop heimdall_ultra_config table."""

    try:
        op.drop_table('heimdall_ultra_config')
        logger.info("[migration 0063] heimdall_ultra_config table dropped")
    except Exception as e:
        logger.warning(f"[migration 0063] heimdall_ultra_config drop failed: {e}")
