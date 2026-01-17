"""Add api_clients table for PACK UD"""

from alembic import op
import sqlalchemy as sa

revision = "0073_pack_ud_api_clients"
down_revision = "0072_pack_uc_rate_limits"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "api_clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("client_type", sa.String(), nullable=False),
        sa.Column("api_key", sa.String(), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    
    op.create_index("ix_api_clients_api_key", "api_clients", ["api_key"])
    op.create_index("ix_api_clients_active", "api_clients", ["active"])


def downgrade():
    op.drop_table("api_clients")
