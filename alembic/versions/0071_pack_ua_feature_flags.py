"""Add feature_flags table for PACK UA"""

from alembic import op
import sqlalchemy as sa

revision = "0071_pack_ua_feature_flags"
down_revision = "0070_pack_tz_system_config"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("group", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_feature_flags_key", "feature_flags", ["key"])
    op.create_index("ix_feature_flags_group", "feature_flags", ["group"])


def downgrade():
    op.drop_table("feature_flags")
