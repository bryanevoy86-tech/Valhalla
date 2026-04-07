"""Add model_providers table for PACK CL12"""

from alembic import op
import sqlalchemy as sa

revision = "cl12_add_model_providers"
down_revision = "cl11_add_strategic_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("vendor", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("default_for_heimdall", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_model_providers_name", "model_providers", ["name"])


def downgrade():
    op.drop_index("ix_model_providers_name", table_name="model_providers")
    op.drop_table("model_providers")
