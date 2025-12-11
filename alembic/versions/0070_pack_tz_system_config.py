"""Add system_config table for PACK TZ"""

from alembic import op
import sqlalchemy as sa

revision = "0070_pack_tz_system_config"
down_revision = "0069_pack_tv_system_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mutable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_system_config_key", "system_config", ["key"])


def downgrade():
    op.drop_table("system_config")
