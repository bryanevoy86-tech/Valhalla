"""Add rate_limit_rules and rate_limit_snapshots for PACK UC"""

from alembic import op
import sqlalchemy as sa

revision = "0072_pack_uc_rate_limits"
down_revision = "0071_pack_ua_feature_flags"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rate_limit_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("max_requests", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "rate_limit_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False),
        sa.Column("max_requests", sa.Integer(), nullable=False),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_started_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("ix_rate_limit_rules_scope_key", "rate_limit_rules", ["scope", "key"])
    op.create_index("ix_rate_limit_snapshots_scope_key", "rate_limit_snapshots", ["scope", "key"])


def downgrade():
    op.drop_table("rate_limit_snapshots")
    op.drop_table("rate_limit_rules")
